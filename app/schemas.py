from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class JobStatus(str, Enum):
    pending = "pending"
    done = "done"
    failed = "failed"


class JobCreate(BaseModel):
    payload: str = Field(..., min_length=1, max_length=200)
    user_id: int


class JobRead(BaseModel):
    id: int
    payload: str
    status: JobStatus
    created_at: datetime
    result: str | None = None
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr = Field(..., max_length=255)


class UserRead(BaseModel):
    id: int
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserWithJobs(UserRead):
    jobs: list[JobRead] = []

class SimilarJob(JobRead):
    distance: float