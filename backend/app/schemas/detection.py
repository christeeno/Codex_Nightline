"""Standardized detection contracts shared by processing engines."""
from typing import Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    @property
    def area(self) -> float:
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)

class Detection(BaseModel):
    type: str
    timestamp: float
    frame_number: int
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: BoundingBox
    tracking_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ProcessingStatistics(BaseModel):
    video_path: str
    frames_processed: int = 0
    candidate_detections: int = 0
    confirmed_potholes: int = 0
    helmet_violations: int = 0
    triple_riding_violations: int = 0
    inference_seconds: float = 0.0
    average_fps: float = 0.0
    errors: list[str] = Field(default_factory=list)

class RoadAnalysisResult(BaseModel):
    detections: list[Detection] = Field(default_factory=list)
    statistics: ProcessingStatistics

class TrafficAnalysisResult(BaseModel):
    detections: list[Detection] = Field(default_factory=list)
    statistics: ProcessingStatistics
