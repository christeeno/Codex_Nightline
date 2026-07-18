"""Engine-neutral batch contracts."""
from typing import Any
from pydantic import BaseModel, Field

class Detection(BaseModel):
    type: str
    timestamp: float = Field(ge=0)
    frame_number: int = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    bounding_box: tuple[float, float, float, float] | None = None
    tracking_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class DetectionBatch(BaseModel):
    detections: list[Detection] = Field(default_factory=list)
    processing_time: float = Field(ge=0)
    frames_processed: int = Field(ge=0)
    video_duration: float = Field(ge=0)
