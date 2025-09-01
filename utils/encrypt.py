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


def encrypt_string(plain_text: str) -> str:
    """
    Encrypt a plain text string using AES-256-GCM and return
    a Base64-encoded string that includes the nonce.

    Args:
        plain_text (str): The message to encrypt.

    Returns:
        str: Encrypted Base64-encoded string.
    """
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plain_text.encode(), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt_string(encrypted_text: str) -> str:
    """
    Decrypt a Base64-encoded AES-256-GCM string.

    Args:
        encrypted_text (str): The encrypted Base64 string.

    Returns:
        str: Decrypted plain text.
    """
    raw = base64.urlsafe_b64decode(encrypted_text.encode())
    nonce, ciphertext = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


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
        if value is None or value.strip() == "":
            return ""
        try:
            raw = base64.urlsafe_b64decode(value.encode())
            if len(raw) < 12:
                return value
            nonce, ciphertext = raw[:12], raw[12:]
            return aesgcm.decrypt(nonce, ciphertext, None).decode()
        except Exception:
            return value

    def validate(self, value):
        """Validate the field value as a string before encryption."""
        if value is not None and not isinstance(value, str):
            self.error("EncryptedStringField only accepts string values.")
