import settings
from celery import Celery

app = Celery(
    "tasks",
    broker=settings.CELERY_broker_url,
    backend=settings.result_backend,
    namespace="CELERY",
    imports="tasks.tasks",
    # timezone="Europe/Warsaw",
)

# app = Celery('tasks')
# app.config_from_object(settings, namespace='CELERY')
app.autodiscover_tasks()
