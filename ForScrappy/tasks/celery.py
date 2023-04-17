from celery import Celery
import settings


app = Celery(
    "tasks",
    broker_url=settings.CELERY_broker_url,
    backend=settings.result_backend,
    namespace="CELERY",
    imports="tasks.tasks",
    timezone="Europe/Warsaw",
)

# app = Celery('tasks')
# app.config_from_object(settings, namespace='CELERY')
app.autodiscover_tasks()
