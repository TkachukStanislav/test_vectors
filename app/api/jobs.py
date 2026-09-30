from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import JOB_CACHE_TTL, job_cache_key, redis_client
from app.db import get_session
from app.embeddings import fake_embedding
from app.metrics import JOBS_CREATED
from app.models import Job, User
from app.schemas import JobCreate, JobRead, SimilarJob
from app.worker import process_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate, session: AsyncSession = Depends(get_session)):
    if await session.get(User, job_data.user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    job = Job(
        payload=job_data.payload,
        user_id=job_data.user_id,
        embedding=fake_embedding(job_data.payload),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    process_job.delay(job.id)
    JOBS_CREATED.inc()
    return job


@router.get("/{job_id}/similar", response_model=list[SimilarJob])
async def similar_jobs(
    job_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
):
    target = await session.get(Job, job_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if target.embedding is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Job has no embedding",
        )

    distance = Job.embedding.cosine_distance(target.embedding).label("distance")
    stmt = (
        select(Job, distance)
        .where(Job.id != job_id, Job.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )
    result = await session.execute(stmt)

    return [
        {**JobRead.model_validate(job).model_dump(), "distance": dist}
        for job, dist in result.all()
    ]


@router.get("/{job_id}", response_model=JobRead, status_code=status.HTTP_200_OK)
async def get_job(job_id: int, session: AsyncSession = Depends(get_session)):
    cached = await redis_client.get(job_cache_key(job_id))
    if cached is not None:
        return JobRead.model_validate_json(cached)

    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    job_read = JobRead.model_validate(job)
    await redis_client.set(job_cache_key(job_id), job_read.model_dump_json(), ex=JOB_CACHE_TTL)
    return job_read


@router.get("", response_model=list[JobRead], status_code=status.HTTP_200_OK)
async def list_jobs(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Job).order_by(Job.created_at.desc(), Job.id.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return result.scalars().all()
