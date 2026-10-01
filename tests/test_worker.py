from sqlalchemy.orm import Session

from app.models import Job, User
from app.schemas import JobStatus
from app.worker import process_job


def create_job(engine, **fields):
    with Session(engine) as session:
        user = User(email="worker@example.com")
        session.add(user)
        session.flush()
        job = Job(user_id=user.id, **fields)
        session.add(job)
        session.commit()
        return job.id


def test_process_job_marks_done(worker_db):
    job_id = create_job(worker_db, payload="hello")

    process_job(job_id)

    with Session(worker_db) as session:
        job = session.get(Job, job_id)
        assert job.status == JobStatus.done
        assert job.result == "olleh"


def test_process_job_is_idempotent(worker_db):
    job_id = create_job(worker_db, payload="hello", status=JobStatus.done, result="already")

    process_job(job_id)

    with Session(worker_db) as session:
        assert session.get(Job, job_id).result == "already"
