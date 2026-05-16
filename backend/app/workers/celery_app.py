from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "netanalyzer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "mark-offline-devices": {
            "task": "app.workers.tasks.mark_offline_devices",
            "schedule": 60.0,
        },
        "cleanup-old-logs": {
            "task": "app.workers.tasks.cleanup_old_logs",
            "schedule": 3600.0,
        },
    },
)
