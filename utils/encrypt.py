import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from mongoengine import StringField

AES_KEY = os.environ.get("AES256_KEY")
if AES_KEY:
    key = base64.urlsafe_b64decode(AES_KEY)
else:
    key = AESGCM.generate_key(bit_length=256)
    print(f"Generated new key: {base64.urlsafe_b64encode(key).decode()}")

aesgcm = AESGCM(key)


class EncryptedStringField(StringField):
    """
    A custom MongoEngine field that transparently encrypts/decrypts
    string values using AES-256-GCM.
    """

    def to_mongo(self, value):
        """Encrypt the string before saving to MongoDB."""
        if value is None:
            return None
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, value.encode(), None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def to_python(self, value):
        """Decrypt the string when loading from MongoDB."""
        if value is None:
            return None
        try:
            raw = base64.urlsafe_b64decode(value.encode())
            nonce, ciphertext = raw[:12], raw[12:]
            return aesgcm.decrypt(nonce, ciphertext, None).decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def validate(self, value):
        """Validate the field value as a string before encryption."""
        if value is not None and not isinstance(value, str):
            self.error("EncryptedStringField only accepts string values.")
