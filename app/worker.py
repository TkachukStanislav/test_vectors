import time

from celery import Celery
from celery.signals import worker_init
from prometheus_client import start_http_server
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.cache import job_cache_key
from app.config import settings
from app.metrics import JOB_PROCESSING_SECONDS, JOBS_PROCESSED
from app.models import Job
from app.schemas import JobStatus

redis_sync = Redis.from_url(settings.redis_url)
celery_app = Celery("mini_petp", broker=settings.celery_broker_url)

# Celery синхронний, тому у воркері синхронний драйвер psycopg замість asyncpg
sync_engine = create_engine(settings.database_url.replace("+asyncpg", "+psycopg"))


@worker_init.connect
def start_metrics_server(**kwargs):
    # воркер — окремий процес, тож віддає свої метрики на власному порту
    start_http_server(8001)


@celery_app.task(
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    max_retries=3,
    acks_late=True,
)
def process_job(job_id: int) -> None:
    with Session(sync_engine) as session:
        job = session.get(Job, job_id)
        # ідемпотентність: повторна доставка тієї ж задачі нічого не зламає
        if job is None or job.status != JobStatus.pending:
            return
        try:
            with JOB_PROCESSING_SECONDS.time():
                time.sleep(3)
                job.result = job.payload[::-1]
            job.status = JobStatus.done
        except Exception:
            job.status = JobStatus.failed
        session.commit()
        redis_sync.delete(job_cache_key(job_id))
        JOBS_PROCESSED.labels(status=job.status.value).inc()
