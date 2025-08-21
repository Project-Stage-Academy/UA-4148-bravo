from mongoengine import Document, StringField, ReferenceField, BooleanField, EnumField
import enum


class UserRoleEnum(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = 'moderator'


class UserRoleDocument(Document):
    role = EnumField(UserRoleEnum, required=True, unique=True)

    meta = {
        "collection": "user_roles"
    }


class UserDocument(Document):
    email = StringField(required=True, unique=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    password = StringField(required=True)
    role = ReferenceField(UserRoleDocument, required=True)
    is_active = BooleanField(default=True)

    meta = {
        "collection": "users"
    }
