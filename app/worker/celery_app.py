"""
Celery application configuration.
"""

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "finsight",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

# Task routes (optional - for multiple queues)
celery_app.conf.task_routes = {
    "app.worker.tasks.process_financial_analysis": {"queue": "analysis"},
}
