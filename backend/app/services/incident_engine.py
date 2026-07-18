"""Merge adapter detections into deduplicated review incidents."""
from uuid import NAMESPACE_URL, uuid5
from app.core.config import get_settings
from app.schemas.incidents import DetectionInput, Incident, ReportSummary
class IncidentEngine:
    def __init__(self): self.settings = get_settings()
    def generate(self, traffic_detections, pothole_detections):
        entries = sorted([DetectionInput.model_validate(item) for item in [*traffic_detections, *pothole_detections]], key=lambda item: item.timestamp); groups = []
        for item in entries:
            if groups and item.type == groups[-1][0].type and item.tracking_id == groups[-1][0].tracking_id and item.timestamp - groups[-1][-1].timestamp <= self.settings.incident_deduplication_seconds: groups[-1].append(item)
            else: groups.append([item])
        result = []
        for group in groups:
            chosen = max(group, key=lambda item: (item.confidence, -(item.blur_score if item.blur_score is not None else float("inf")), item.object_area or 0)); plate = max((item for item in group if item.license_plate), key=lambda item: item.ocr_confidence or 0, default=chosen); timestamp = group[0].timestamp
            result.append(Incident(id=str(uuid5(NAMESPACE_URL, f"{chosen.type}:{chosen.tracking_id}:{timestamp:.3f}")), type=chosen.type, timestamp=timestamp, confidence=max(item.confidence for item in group), status=self.settings.incident_default_status, license_plate=plate.license_plate or self.settings.unknown_label, ocr_confidence=plate.ocr_confidence or 0, evidence_image=chosen.evidence_image, metadata={"tracking_id": chosen.tracking_id, "detection_count": len(group), "evidence_frame_index": chosen.frame_index}))
        return result
    def generate_report(self, incidents, *, video_duration_seconds, processing_time_seconds):
        items = list(incidents); return ReportSummary(video_duration_seconds=video_duration_seconds, processing_time_seconds=processing_time_seconds, helmet_violations=sum(item.type == "helmet_violation" for item in items), triple_riding=sum(item.type == "triple_riding" for item in items), potholes=sum(item.type == "pothole" for item in items), reports_ready=len(items))
