"""Persistent report metadata for uploaded videos."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Report(Base):
    """A submitted video and the metadata discovered while processing it."""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    video_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    resolution: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    frame_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    codec: Mapped[str | None] = mapped_column(String(16), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    # Contract fields. Legacy metadata above remains available to the existing
    # video-upload flow while frontend integrations use these stable names.
    video_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    submission_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="NOT_SUBMITTED"
    )
    reward_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tracking_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class Incident(Base):
    """A reviewable item of evidence produced for one report."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    license_plate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    bounding_box: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    approved: Mapped[bool] = mapped_column(default=False, nullable=False)
    tracking_object: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reward_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    report: Mapped[Report] = relationship(back_populates="incidents")
    evidence: Mapped["Evidence | None"] = relationship(
        back_populates="incident", uselist=False, cascade="all, delete-orphan"
    )


class Evidence(Base):
    """The one best evidence frame linked to an incident."""

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id"), nullable=False, unique=True, index=True
    )
    image_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    license_plate: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    incident: Mapped[Incident] = relationship(back_populates="evidence")


class Submission(Base):
    """A local record of a mock government-submission attempt."""

    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    government_tracking_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    submission_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NOT_SUBMITTED")
    response_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    report: Mapped[Report] = relationship(back_populates="submissions")
