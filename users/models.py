from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, DataError
from django.utils import timezone
from django.forms.models import model_to_dict
from validation.validate_email import validate_email_custom
from validation.validate_string_fields import validate_max_length
from validation.validate_role import validate_role_exists


class ActiveUserManager(models.Manager):
    """Manager that returns only active users."""

    def get_queryset(self):
        """
        Retrieve a queryset filtering only active users.

        Returns:
            QuerySet: A queryset of users with is_active=True.
        """
        return super().get_queryset().filter(is_active=True)


class CustomUserManager(BaseUserManager):
    """Manager for creating regular and super users."""

    def create_user(self, email, password=None, **other_fields):
        """
        Create and save a regular user with the given email and password.

        Args:
            email (str): The user's email address.
            password (str, optional): The user's password.
            **other_fields: Additional fields for the user model.

        Raises:
            ValueError: If email is not provided or invalid.

        Returns:
            User: The created user instance.
        """
        validate_max_length(email, 50, "Email")
        
        if self.model.all_objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        
        validate_email_custom(email)
        
        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **other_fields):
        """
        Create and save a superuser with the given email and password.

        Args:
            email (str): The superuser's email address.
            password (str, optional): The superuser's password.
            **other_fields: Additional fields for the user model.

        Returns:
            User: The created superuser instance.
        """
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **other_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model.

    Attributes:
        user_id (AutoField): Primary key.
        first_name (str): User's first name.
        last_name (str): User's last name.
        email (str): User's email address (unique).
        password (str): Hashed password.
        user_phone (str, optional): User's phone number.
        title (str, optional): User's job title.
        role (str): User role.
        created_at (datetime): Record creation timestamp.
        updated_at (datetime): Record last update timestamp.
        is_active (bool): User active status.
        is_staff (bool): User staff status.
    """

    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, max_length=50)
    password = models.CharField(max_length=128)
    user_phone = models.CharField(max_length=20, null=True, blank=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    role = models.ForeignKey(
        'UserRole',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users',
        help_text="Current role of the user"
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()
    active_users = ActiveUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        """
        Return a string representation of the user.

        Returns:
            str: String with user details.
        """
        return (
            f"'id': {self.user_id}, "
            f"'first_name': '{self.first_name}', "
            f"'last_name': '{self.last_name}', "
            f"'email': '{self.email}', "
            f"'user_phone': '{self.user_phone}', "
            f"'title': '{self.title}', "
            f"'role': '{self.role.role if self.role else None}', "
            f"'created_at': {int(self.created_at.timestamp())}, "
            f"'updated_at': {int(self.updated_at.timestamp())}, "
            f"'is_active': {self.is_active}, "
            f"'is_staff': {self.is_staff}"
        )

    def to_dict(self):
        """
        Convert the user instance to a dictionary.

        Returns:
            dict: Dictionary containing user data.
        """
        data = model_to_dict(
            self,
            fields=[
                "user_id", "first_name", "last_name", "email",
                "user_phone", "title", "role", "created_at",
                "updated_at", "is_active", "is_staff"
            ]
        )
        data["created_at"] = int(self.created_at.timestamp())
        data["updated_at"] = int(self.updated_at.timestamp())
        data["role"] = self.role.role if self.role else None
        return data

    @classmethod
    def get_by_id(cls, user_id):
        """
        Retrieve a user by their ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            User or None: The user instance if found, else None.
        """
        return cls.active_users.filter(user_id=user_id).first()

    @classmethod
    def get_by_email(cls, email):
        """
        Retrieve a user by their email address.

        Args:
            email (str): The user's email.

        Returns:
            User or None: The user instance if found, else None.
        """
        return cls.active_users.filter(email=email).first()

    @classmethod
    def create(cls, email, password, first_name, last_name,
               user_phone=None, title=None, role=None, **other_fields):
        """
        Create a new user with field validation.

        Args:
            email (str): User email.
            password (str): User password.
            first_name (str): First name.
            last_name (str): Last name.
            user_phone (str, optional): Phone number.
            title (str, optional): Job title.
            role (str, optional): User role.
            **other_fields: Additional fields.

        Raises:
            ValueError: If validation fails or email already exists.

        Returns:
            User: The created user instance.
        """
        validate_email_custom(email)

        if cls.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")

        validate_max_length(email, 50, "Email")
        validate_max_length(first_name, 50, "First name")
        validate_max_length(last_name, 50, "Last name")
        if user_phone:
            validate_max_length(user_phone, 20, "User phone")
        if title:
            validate_max_length(title, 100, "Title")
        role_obj = None
        if role:
            role_obj = validate_role_exists(role)
        if not password or not isinstance(password, str) or len(password) < 8:
            raise ValidationError("Password must be a string at least 8 characters long")

        user = cls(
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_phone=user_phone,
            title=title,
            role=role_obj,
            **other_fields
        )
        user.set_password(password)
        try:
            user.save()
        except (IntegrityError, DataError) as e:
            raise ValueError(f"Database error: {e}")
        return user

    def update(self, **kwargs):
        """
        Update user fields with validation.

        Args:
            **kwargs: Fields to update.

        Raises:
            ValueError: If validation fails.

        Returns:
            User: Updated user instance.
        """

        def validate_first_name(v):
            return isinstance(v, str) and len(v) <= 50

        def validate_last_name(v):
            return isinstance(v, str) and len(v) <= 50

        def validate_user_phone(v):
            return v is None or (isinstance(v, str) and len(v) <= 20)

        def validate_title(v):
            return v is None or (isinstance(v, str) and len(v) <= 100)

        def validate_role(v):
            return isinstance(v, str) and UserRole.objects.filter(role=v).exists()

        def validate_is_active(v):
            return isinstance(v, bool)

        def validate_is_staff(v):
            return isinstance(v, bool)

        def validate_email_field(v):
            if not isinstance(v, str) or len(v) > 50:
                return False
            try:
                validate_email_custom(v)
                return True
            except ValidationError:
                return False

        allowed_fields = {
            'first_name': validate_first_name,
            'last_name': validate_last_name,
            'user_phone': validate_user_phone,
            'title': validate_title,
            'role': validate_role,
            'email': validate_email_field,
            'is_active': validate_is_active,
            'is_staff': validate_is_staff
        }

        for attr, validator in allowed_fields.items():
            if attr in kwargs:
                value = kwargs[attr]
                if not validator(value):
                    raise ValidationError(f"Invalid value for field '{attr}': {value}")
                
                if attr == 'role':
                    role_obj = validate_role_exists(value)
                    setattr(self, 'role', role_obj)
                else:
                    setattr(self, attr, value)

        if 'password' in kwargs:
            password = kwargs['password']
            if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
                raise ValidationError("Password must be a string between 8 and 128 characters.")
            
            if not self.check_password(password):
                self.set_password(password)

        self.save()
        return self

    @classmethod
    def deactivate_by_id(cls, user_id):
        """
        Deactivate a user by setting is_active to False.

        Args:
            user_id (int): The ID of the user to deactivate.

        Returns:
            bool: True if user was found and deactivated, else False.
        """
        user = cls.active_users.filter(user_id=user_id, is_active=True).first()
        if user:
            user.is_active = False
            user.save()
            return True
        return False

    @classmethod
    def get_all(cls):
        """
        Retrieve all users.

        Returns:
            QuerySet: QuerySet of all users.
        """
        return cls.active_users.all()


class UserRole(models.Model):
    """
    User role model.

    Attributes:
        role (str): Role name.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
    """
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'
        MODERATOR = 'moderator', 'Moderator'

    role = models.CharField(max_length=20, unique=True, choices=Role.choices)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_roles'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        """
        String representation of the user role.

        Returns:
            str: Role name.
        """
        return self.role
    
    def clean(self):
        if self.role not in dict(self.Role.choices):
            raise ValidationError(f"Invalid role: {self.role}")

    def save(self, *args, **kwargs):
        self.clean() 
        super().save(*args, **kwargs)
