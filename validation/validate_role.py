from django.core.exceptions import ValidationError

def validate_role_exists(role_name):
    """
    Checks if a role with the given name exists in the database.

    Args:
        role_name (str): The name of the role to validate.

    Raises:
        ValidationError: If no role with the specified name exists.

    Returns:
        UserRole: The role object if found.
    """
    from users.models import UserRole
    role_obj = UserRole.objects.filter(role=role_name).first()
    if not role_obj:
        raise ValidationError(f"Role '{role_name}' does not exist")
    return role_obj

def get_default_role_id():
    """
    Retrieve the ID of the default user role ('user') from the database.

    If the default role does not exist, it will be created automatically.

    The import of the UserRole model is done inside the function to avoid
    potential circular import issues or errors during Django migrations
    when the models might not yet be fully loaded.

    Returns:
        int: The primary key (ID) of the default 'user' role.
    """
    from users.models import UserRole
    default_role = UserRole.objects.filter(role=UserRole.Role.USER).first()
    if default_role:
        return default_role.id
    default_role = UserRole.objects.create(role=UserRole.Role.USER)
    return default_role.id