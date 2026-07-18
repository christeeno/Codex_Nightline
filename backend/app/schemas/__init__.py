"""Pydantic schemas shared by API endpoints and services."""
from app.schemas.detection import BoundingBox, Detection, ProcessingStatistics, RoadAnalysisResult, TrafficAnalysisResult
from app.schemas.detections import DetectionBatch
from app.schemas.incidents import BoundingBox as IncidentBoundingBox, DetectionInput, Incident, IncidentGenerationRequest, IncidentGenerationResponse, LicensePlateResult, ReportSummary
from app.schemas.reports import ProgressResponse, ReportResponse, VideoMetadataResponse

__all__ = ["Detection", "DetectionBatch", "BoundingBox", "IncidentBoundingBox", "DetectionInput", "Incident", "IncidentGenerationRequest", "IncidentGenerationResponse", "LicensePlateResult", "ReportSummary", "ProcessingStatistics", "RoadAnalysisResult", "TrafficAnalysisResult", "ProgressResponse", "ReportResponse", "VideoMetadataResponse"]
