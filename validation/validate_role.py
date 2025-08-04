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