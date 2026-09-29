from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.schemas import JobStatus


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="jobstatus"),
        default=JobStatus.pending,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )