import time

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Job
from app.schemas import JobStatus

celery_app = Celery("mini_petp", broker=settings.celery_broker_url)

# Celery синхронний, тому у воркері синхронний драйвер psycopg замість asyncpg
sync_engine = create_engine(settings.database_url.replace("+asyncpg", "+psycopg"))


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
            time.sleep(3)
            job.result = job.payload[::-1]
            job.status = JobStatus.done
        except Exception:
            job.status = JobStatus.failed
        session.commit()
