"""
Celery 配置
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "tsla_simulator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.backtest_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,  # 公平调度
)
