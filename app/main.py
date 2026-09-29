
from fastapi import FastAPI, HTTPException, Query, status

from app.schemas import JobCreate, JobRead

app = FastAPI()

from fastapi import Depends                      # додай до наявного імпорту з fastapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Job


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


@app.post("/jobs", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate, session: AsyncSession = Depends(get_session)):
    job = Job(payload=job_data.payload)
    session.add(job)
    await session.commit(   )
    await session.refresh(job)
    return job

@app.get("/jobs/{job_id}", response_model=JobRead, status_code=status.HTTP_200_OK)
async def get_job(job_id: int, session: AsyncSession = Depends(get_session)):
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@app.get("/jobs", response_model=list[JobRead], status_code=status.HTTP_200_OK)
async def list_jobs(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Job).order_by(Job.created_at.desc(), Job.id.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return result.scalars().all()