import logging

from celery import Celery, shared_task

app = Celery('investments')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

logger = logging.getLogger(__name__)


@shared_task
def recalc_investment_shares_task(project_id):
    """
    Celery task to recalculate investment shares for all subscriptions
    related to a given project.

    Args:
        project_id (int): The primary key of the project whose subscriptions
                          need their investment shares recalculated.

    This task fetches the project by ID and calls the recalculation function.
    If the project does not exist, the task exits silently.
    """
    from projects.models import Project
    from investments.services.investment_share_service import recalculate_investment_shares

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.warning(f"Project with id={project_id} not found.")
        return

    recalculate_investment_shares(project)
