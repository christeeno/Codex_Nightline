"""Upload and progress response contracts."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class VideoMetadataResponse(BaseModel):
    filename: str
    resolution: str
    fps: float
    frame_count: int
    duration: float
    codec: str

class ReportResponse(BaseModel):
    id: str
    status: str
    metadata: VideoMetadataResponse

class ProgressResponse(BaseModel):
    report_id: str
    frames_read: int = Field(ge=0)
    frames_remaining: int = Field(ge=0)
    current_timestamp: float = Field(ge=0)
    percent_complete: float = Field(ge=0, le=100)
    estimated_time_remaining: float = Field(ge=0)
    current_stage: str
    status: Literal["uploaded", "processing", "completed", "failed"]
    updated_at: datetime
    error: str | None = None
