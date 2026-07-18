"""Public contracts for license recognition and incident generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BoundingBox(BaseModel):
    """A pixel bounding box expressed as left/top/right/bottom coordinates."""

    model_config = ConfigDict(frozen=True)

    left: float
    top: float
    right: float
    bottom: float

    @property
    def area(self) -> float:
        """Return a non-negative area for evidence selection."""
        return max(0.0, self.right - self.left) * max(0.0, self.bottom - self.top)


class LicensePlateResult(BaseModel):
    """A bounded, confidence-qualified outcome of plate recognition."""

    license_plate: str
    ocr_confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: BoundingBox | None = None
    plate_detected: bool = False


class DetectionInput(BaseModel):
    """Normalized adapter output accepted by the incident engine.

    Traffic and pothole engines remain isolated: their adapters map their own
    detections to this transport contract rather than exposing engine objects.
    """

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    type: str
    timestamp: float = Field(ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)
    tracking_id: str | None = None
    evidence_image: str | None = None
    bounding_box: BoundingBox | None = None
    motorcycle_bounding_box: BoundingBox | None = None
    frame_index: int | None = Field(default=None, ge=0)
    blur_score: float | None = Field(default=None, ge=0.0)
    object_area: float | None = Field(default=None, ge=0.0)
    license_plate: str | None = None
    ocr_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "_")
        if not normalized:
            raise ValueError("detection type must not be empty")
        return normalized


class Incident(BaseModel):
    """The standard human-reviewable incident schema for every frontend."""

    id: str
    type: str
    timestamp: float = Field(ge=0.0)
    confidence: float = Field(ge=0.0, le=1.0)
    status: str
    approved: bool = False
    license_plate: str
    ocr_confidence: float = Field(ge=0.0, le=1.0)
    evidence_image: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentGenerationRequest(BaseModel):
    """Payload for merging traffic and pothole adapter detections."""

    traffic_detections: list[DetectionInput] = Field(default_factory=list)
    pothole_detections: list[DetectionInput] = Field(default_factory=list)
    video_duration_seconds: float = Field(default=0.0, ge=0.0)
    processing_time_seconds: float = Field(default=0.0, ge=0.0)


class ReportSummary(BaseModel):
    """Aggregate report object; PDF and government submission are excluded."""

    video_duration_seconds: float = Field(ge=0.0)
    processing_time_seconds: float = Field(ge=0.0)
    helmet_violations: int = Field(ge=0)
    triple_riding: int = Field(ge=0)
    potholes: int = Field(ge=0)
    reports_ready: int = Field(ge=0)


class IncidentGenerationResponse(BaseModel):
    """Generated incidents and their processing report."""

    incidents: list[Incident]
    report: ReportSummary
