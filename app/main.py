from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query, status

from app.schemas import JobCreate, JobRead, JobStatus

app = FastAPI()

# Сховище даних (зберігаємо звичайні dict, а не схеми відповідей Pydantic)
jobs: dict[int, dict] = {}
current_id = 0


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


@app.post("/jobs", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate):
    global current_id
    current_id += 1

    # Зберігаємо сирі дані окремо від Pydantic-схеми відповіді
    job_record = {
        "id": current_id,
        "payload": job_data.payload,
        "status": JobStatus.pending,
        "created_at": datetime.now(timezone.utc),
    }
    jobs[current_id] = job_record
    return job_record


@app.get("/jobs/{job_id}", response_model=JobRead, status_code=status.HTTP_200_OK)
async def get_job(job_id: int):
    job_record = jobs.get(job_id)
    if not job_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job_record


@app.get("/jobs", response_model=list[JobRead], status_code=status.HTTP_200_OK)
async def list_jobs(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    all_jobs = list(jobs.values())
    return all_jobs[offset : offset + limit]