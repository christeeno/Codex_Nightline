"""Pydantic request and response contracts for the public REST interface."""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IncidentStatus, IncidentType, ReportStatus, SubmissionStatus


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UploadVideoRequest(Schema):
    video_name: str = Field(min_length=1, max_length=255)
    video_path: str = Field(min_length=1, max_length=2048)
    video_duration: Optional[float] = Field(default=None, ge=0)


class AnalyzeVideoRequest(Schema):
    force: bool = False


class ApproveIncidentRequest(Schema):
    tracking_object: Optional[str] = Field(default=None, max_length=255)


class RejectIncidentRequest(Schema):
    reason: Optional[str] = Field(default=None, max_length=500)


class SubmitReportRequest(Schema):
    government_tracking_id: Optional[str] = Field(default=None, max_length=255)


class EvidenceResponse(Schema):
    id: UUID
    incident_id: UUID
    image_path: str
    thumbnail_path: Optional[str]
    frame_number: int
    license_plate: Optional[str]
    ocr_confidence: Optional[float]
    metadata_json: dict[str, Any]


class IncidentResponse(Schema):
    id: UUID
    report_id: UUID
    type: IncidentType
    timestamp: float
    confidence: float
    severity: str
    status: IncidentStatus
    approved: bool
    tracking_object: Optional[str]
    evidence: Optional[EvidenceResponse] = None


class SubmissionResponse(Schema):
    id: UUID
    report_id: UUID
    submitted_at: datetime
    government_tracking_id: Optional[str]
    submission_status: SubmissionStatus
    response_json: dict[str, Any]


class ReportResponse(Schema):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: ReportStatus
    video_name: str
    video_path: str
    video_duration: Optional[float]
    processing_time: Optional[float]
    submission_status: SubmissionStatus
    reward_status: Optional[str]
    tracking_id: Optional[str]
    summary_json: dict[str, Any]
    incidents: list[IncidentResponse] = Field(default_factory=list)
    submissions: list[SubmissionResponse] = Field(default_factory=list)


class UploadResponse(Schema):
    report_id: UUID
    filename: str
    duration: Optional[float]
    status: ReportStatus


class ProgressResponse(Schema):
    report_id: UUID
    status: ReportStatus
    progress_percent: int = Field(ge=0, le=100)
    message: str


class RecentActivityResponse(Schema):
    report_id: UUID
    video_name: str
    status: ReportStatus
    created_at: datetime


class DashboardSummaryResponse(Schema):
    reports_submitted: int = Field(ge=0)
    verified_reports: int = Field(ge=0)
    pending_reports: int = Field(ge=0)
    rejected_reports: int = Field(ge=0)
    rewards_earned: float = Field(ge=0)
    recent_activity: list[RecentActivityResponse] = Field(default_factory=list)


T = TypeVar("T")


class ApiResponse(Schema, Generic[T]):
    success: bool = True
    message: str
    data: T


class ErrorResponse(Schema):
    success: bool = False
    message: str
    errors: list[Any] = Field(default_factory=list)
