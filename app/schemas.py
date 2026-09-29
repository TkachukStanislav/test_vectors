from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    pending = "pending"
    done = "done"
    failed = "failed"


class JobCreate(BaseModel):
    payload: str = Field(..., min_length=1, max_length=200)


class JobRead(BaseModel):
    id: int
    payload: str
    status: JobStatus
    created_at: datetime
    result: str | None = None
    model_config = ConfigDict(from_attributes=True)