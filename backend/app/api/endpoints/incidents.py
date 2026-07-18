"""Incident generation endpoint fed by isolated engine adapters."""

from fastapi import APIRouter

from app.schemas.incidents import IncidentGenerationRequest, IncidentGenerationResponse
from app.services.incident_engine import IncidentEngine


router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("/generate", response_model=IncidentGenerationResponse)
def generate_incidents(payload: IncidentGenerationRequest) -> IncidentGenerationResponse:
    """Create review-ready incidents and their summary report."""
    engine = IncidentEngine()
    incidents = engine.generate(payload.traffic_detections, payload.pothole_detections)
    report = engine.generate_report(
        incidents,
        video_duration_seconds=payload.video_duration_seconds,
        processing_time_seconds=payload.processing_time_seconds,
    )
    return IncidentGenerationResponse(incidents=incidents, report=report)
