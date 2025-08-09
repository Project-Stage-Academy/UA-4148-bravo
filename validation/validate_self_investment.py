from django.core.exceptions import ValidationError

def validate_self_investment(investor, project):
    """
    Validates that an investor is not investing in their own startup's project.

    Args:
        investor: The Investor instance making the subscription.
        project: The Project instance receiving the investment.

    Raises:
        ValidationError: If the investor is the owner of the project's startup.
    """
    if (
        investor and project and
        hasattr(project, 'startup') and
        project.startup and
        project.startup.user_id == investor.user_id
    ):
        raise ValidationError("Investors cannot invest in their own startup's project.")
