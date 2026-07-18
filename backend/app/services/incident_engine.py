"""Merge adapter detections into deduplicated, reviewable incidents."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.core.config import Settings, get_settings
from app.schemas.detection import Detection
from app.schemas.incidents import DetectionInput, Incident, ReportSummary


logger = logging.getLogger(__name__)


class IncidentEngine:
    """Convert traffic and pothole adapter outputs into the standard schema."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def generate(
        self,
        traffic_detections: Iterable[DetectionInput | Detection | dict[str, Any]],
        pothole_detections: Iterable[DetectionInput | Detection | dict[str, Any]],
    ) -> list[Incident]:
        """Merge, deduplicate, select evidence, and sort incidents by time."""
        detections = [self._coerce(item) for item in [*traffic_detections, *pothole_detections]]
        groups = self._deduplicate(sorted(detections, key=lambda item: item.timestamp))
        return sorted((self._make_incident(group) for group in groups), key=lambda item: item.timestamp)

    def generate_report(
        self,
        incidents: Iterable[Incident],
        *,
        video_duration_seconds: float,
        processing_time_seconds: float,
    ) -> ReportSummary:
        """Generate report objects only; no PDF or external submission occurs."""
        incident_list = list(incidents)
        report = ReportSummary(
            video_duration_seconds=video_duration_seconds,
            processing_time_seconds=processing_time_seconds,
            helmet_violations=sum(item.type == "helmet_violation" for item in incident_list),
            triple_riding=sum(item.type == "triple_riding" for item in incident_list),
            potholes=sum(item.type == "pothole" for item in incident_list),
            reports_ready=len(incident_list),
        )
        logger.info("Report generated", extra={"reports_ready": report.reports_ready})
        return report

    def _deduplicate(self, detections: list[DetectionInput]) -> list[list[DetectionInput]]:
        groups: list[list[DetectionInput]] = []
        for detection in detections:
            matching_group = next((group for group in reversed(groups) if self._matches_group(detection, group)), None)
            if matching_group is None:
                groups.append([detection])
            else:
                matching_group.append(detection)
        return groups

    def _matches_group(self, detection: DetectionInput, group: list[DetectionInput]) -> bool:
        previous = group[-1]
        return (
            detection.type == previous.type
            and detection.tracking_id == previous.tracking_id
            and detection.timestamp - previous.timestamp <= self.settings.incident_deduplication_seconds
        )

    def _make_incident(self, group: list[DetectionInput]) -> Incident:
        evidence = self._select_evidence(group)
        plate_source = self._select_plate(group)
        timestamp = min(item.timestamp for item in group)
        tracking_id = evidence.tracking_id or "untracked"
        incident = Incident(
            id=str(uuid5(NAMESPACE_URL, f"{evidence.type}:{tracking_id}:{timestamp:.3f}")),
            type=evidence.type,
            timestamp=timestamp,
            confidence=max(item.confidence for item in group),
            status=self.settings.incident_default_status,
            approved=False,
            license_plate=plate_source.license_plate or self.settings.unknown_label,
            ocr_confidence=plate_source.ocr_confidence or 0.0,
            evidence_image=evidence.evidence_image,
            metadata={
                "tracking_id": evidence.tracking_id,
                "detection_count": len(group),
                "evidence_frame_index": evidence.frame_index,
            },
        )
        logger.info("Incident created", extra={"incident_id": incident.id, "type": incident.type})
        return incident

    def _select_evidence(self, group: list[DetectionInput]) -> DetectionInput:
        """Rank neighbouring event frames by confidence, blur, and object area."""
        selected = max(group, key=self._evidence_rank)
        logger.info("Evidence selected", extra={"frame_index": selected.frame_index, "confidence": selected.confidence})
        return selected

    def _evidence_rank(self, detection: DetectionInput) -> tuple[float, float, float]:
        blur = detection.blur_score if detection.blur_score is not None else float("inf")
        area = detection.object_area
        if area is None and detection.bounding_box is not None:
            area = detection.bounding_box.area
        return (detection.confidence, -blur, area or 0.0)

    def _select_plate(self, group: list[DetectionInput]) -> DetectionInput:
        known = [item for item in group if item.license_plate and item.license_plate != self.settings.unknown_label]
        return max(known or group, key=lambda item: item.ocr_confidence or 0.0)

    @staticmethod
    def _coerce(item: DetectionInput | Detection | dict[str, Any]) -> DetectionInput:
        if isinstance(item, DetectionInput):
            return item
        if isinstance(item, Detection):
            payload = item.model_dump()
            payload["frame_index"] = payload.pop("frame_number")
        else:
            payload = dict(item)
            if "frame_number" in payload and "frame_index" not in payload:
                payload["frame_index"] = payload.pop("frame_number")
        box = payload.get("bounding_box")
        if isinstance(box, (tuple, list)):
            left, top, right, bottom = box
            payload["bounding_box"] = {"left": left, "top": top, "right": right, "bottom": bottom}
        elif isinstance(box, dict) and {"x1", "y1", "x2", "y2"}.issubset(box):
            payload["bounding_box"] = {"left": box["x1"], "top": box["y1"], "right": box["x2"], "bottom": box["y2"]}
        return DetectionInput.model_validate(payload)
