from notifications.models import Notification
from investors.models import Investor
from startups.models import Startup


def notify_follow(investor: Investor, startup: Startup) -> Notification:
    """
    Creates a 'follow' notification when an investor follows a startup.
    """
    investor_user = investor.user
    display_name = investor_user.first_name or investor_user.email.split("@")[0]

    title = "New follower"
    body = f"{display_name} followed your startup “{startup.company_name}”."

    return Notification.objects.create(
        investor=investor,
        startup=startup,
        type=Notification.Type.FOLLOW,
        title=title,
        body=body,
    )