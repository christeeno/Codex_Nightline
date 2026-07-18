"""The full-video analysis worker used by the public analysis endpoint.

The worker reads every frame in order.  Inference is scheduled by timestamp at
the configured engine rates, which keeps work bounded without imposing a video
duration or frame-count limit.  Models are cached at module scope and therefore
loaded once per backend process.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from time import monotonic
from typing import Any

import numpy as np
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.adapters.license_plate_detector import OpenCVPlateDetector
from app.adapters.paddle_ocr import PaddleOCRAdapter
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.report import Incident, Report
from app.schemas.incidents import BoundingBox
from app.services.frame_sampling import FrameSampler
from app.services.license_plate_recognition import LicensePlateRecognitionService
from app.services.video_reader import VideoOpenError, VideoReader

logger = logging.getLogger(__name__)
_models: dict[str, Any] = {}


class ModelLoadError(RuntimeError):
    """Raised when a configured, required model cannot be loaded."""


def _model(name: str, path: str) -> Any:
    """Load a YOLO model once and retain it for all later reports."""
    if name in _models:
        return _models[name]
    source = Path(path)
    if not source.is_file() and not path.startswith(("http://", "https://")):
        raise ModelLoadError(f"{name} weights are missing at {path}. See README model setup.")
    try:
        from ultralytics import YOLO

        _models[name] = YOLO(path)
        logger.info("%s model loaded from %s", name, path)
        return _models[name]
    except Exception as exc:  # pragma: no cover - depends on local model runtime
        raise ModelLoadError(f"Unable to load {name} model: {exc}") from exc


def _boxes(model: Any, image: np.ndarray, confidence: float) -> list[tuple[str, float, BoundingBox]]:
    """Normalize Ultralytics output without depending on a model-specific class map."""
    result = model.predict(image, conf=confidence, verbose=False)
    if not result:
        return []
    names = result[0].names
    normalized: list[tuple[str, float, BoundingBox]] = []
    for box in result[0].boxes or []:
        class_id = int(float(box.cls.item()))
        label = str(names.get(class_id, class_id) if isinstance(names, dict) else names[class_id]).lower()
        x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
        if x2 > x1 and y2 > y1:
            normalized.append((label, float(box.conf.item()), BoundingBox(left=x1, top=y1, right=x2, bottom=y2)))
    return normalized


def _overlaps(first: BoundingBox, second: BoundingBox) -> bool:
    left, top = max(first.left, second.left), max(first.top, second.top)
    right, bottom = min(first.right, second.right), min(first.bottom, second.bottom)
    return right > left and bottom > top


def _traffic_candidates(model: Any, image: np.ndarray, confidence: float) -> list[tuple[float, BoundingBox]]:
    """Require an explicit motorcycle and no-helmet label to prevent false positives.

    In particular, pedestrians and cars cannot produce an event because neither
    is accepted as a motorcycle.  A helmet label alone is not evidence of a
    violation.
    """
    detections = _boxes(model, image, confidence)
    motorcycles = [box for label, _, box in detections if any(word in label for word in ("motorcycle", "motorbike", "two_wheeler"))]
    missing_helmets = [(score, box) for label, score, box in detections if "helmet" in label and any(word in label for word in ("no", "without", "missing"))]
    return [(score, motorcycle) for score, helmet in missing_helmets for motorcycle in motorcycles if _overlaps(helmet, motorcycle)]


def _pothole_candidates(model: Any, image: np.ndarray, confidence: float) -> list[tuple[float, BoundingBox]]:
    """Return only the approved pothole class; cracks are intentionally excluded."""
    return [(score, box) for label, score, box in _boxes(model, image, confidence) if label.strip() in {"pothole", "0"}]


def _save_evidence(image: np.ndarray, report_id: str, frame_number: int) -> str | None:
    target = Path(get_settings().evidence_path) / f"{report_id}-{frame_number}.jpg"
    try:
        import cv2
        return f"evidence/{target.name}" if cv2.imwrite(str(target), image) else None
    except Exception:
        logger.warning("Evidence frame could not be written", exc_info=True)
        return None


def _set_progress(report: Report, *, read: int, stage: str, percent: float, timestamp: float = 0.0) -> None:
    summary = dict(report.summary_json or {})
    summary["progress"] = {
        "frames_read": read,
        "current_timestamp": round(timestamp, 3),
        "percent_complete": round(min(100.0, max(0.0, percent)), 2),
        "current_stage": stage,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    report.summary_json = summary


def _record(
    database: Session,
    report: Report,
    recent: dict[str, Incident],
    *,
    kind: str,
    title: str,
    timestamp: float,
    frame_number: int,
    confidence: float,
    image: np.ndarray,
    motorcycle: BoundingBox | None = None,
) -> None:
    """Deduplicate neighbouring observations while retaining best evidence."""
    previous = recent.get(kind)
    if previous is not None and timestamp - previous.timestamp <= settings.incident_deduplication_seconds:
        if confidence <= previous.confidence:
            return
        previous.timestamp, previous.frame_number, previous.confidence = timestamp, frame_number, confidence
        previous.evidence_path = _save_evidence(image, report.id, frame_number)
        return
    plate, ocr_confidence = settings.unknown_label, 0.0
    if kind == "HELMET_VIOLATION" and motorcycle is not None:
        recognition = LicensePlateRecognitionService(OpenCVPlateDetector(), PaddleOCRAdapter()).recognize(
            image, helmet_violation=True, motorcycle_bounding_box=motorcycle
        )
        plate, ocr_confidence = recognition.license_plate, recognition.ocr_confidence
    incident = Incident(
        report_id=report.id,
        type=kind,
        title=title,
        timestamp=timestamp,
        frame_number=frame_number,
        confidence=confidence,
        license_plate=plate,
        ocr_confidence=ocr_confidence,
        evidence_path=_save_evidence(image, report.id, frame_number),
        bounding_box=[motorcycle.left, motorcycle.top, motorcycle.right, motorcycle.bottom] if motorcycle else None,
        severity="HIGH" if confidence >= 0.8 else "MEDIUM",
        reward_credits=150 if kind == "HELMET_VIOLATION" else 80,
        details={"ocr_attempted": kind == "HELMET_VIOLATION", "source": "approved_model"},
    )
    database.add(incident)
    database.flush()
    recent[kind] = incident


settings = get_settings()


def process_report(report_id: str) -> None:
    """Run traffic, road, OCR, and incident generation for one stored video."""
    database: Session = SessionLocal()
    started = monotonic()
    try:
        report = database.get(Report, report_id)
        if report is None:
            return
        # Clearing stale results makes a deliberate re-analysis deterministic.
        database.execute(delete(Incident).where(Incident.report_id == report.id))
        traffic_model = _model("Bike-Helmet-Detectionv2", settings.helmet_model_path)
        pothole_model = _model("PeterHdd/pothole-detection-yolo", settings.model_path)
        traffic_sampler, road_sampler = FrameSampler(settings.traffic_fps), FrameSampler(settings.road_fps)
        traffic_next = road_next = 0.0
        recent: dict[str, Incident] = {}
        with VideoReader(report.video_path) as reader:
            metadata = reader.metadata
            for frame in reader.frames():
                traffic_due, traffic_next = traffic_sampler.accepts(frame, traffic_next)
                road_due, road_next = road_sampler.accepts(frame, road_next)
                if traffic_due:
                    for confidence, motorcycle in _traffic_candidates(traffic_model, frame.image, settings.pothole_confidence):
                        _record(database, report, recent, kind="HELMET_VIOLATION", title="Missing Helmet Detection", timestamp=frame.timestamp, frame_number=frame.frame_number, confidence=confidence, image=frame.image, motorcycle=motorcycle)
                if road_due:
                    for confidence, _ in _pothole_candidates(pothole_model, frame.image, settings.pothole_confidence):
                        _record(database, report, recent, kind="POTHOLE", title="Road Surface Pothole", timestamp=frame.timestamp, frame_number=frame.frame_number, confidence=confidence, image=frame.image)
                if frame.frame_number % max(1, int(metadata.fps)) == 0:
                    _set_progress(report, read=frame.frame_number + 1, stage="Traffic and road analysis", percent=(frame.frame_number + 1) / metadata.frame_count * 100, timestamp=frame.timestamp)
                    database.commit()
            report.processing_time = monotonic() - started
            report.completed_at = datetime.now(timezone.utc)
            report.status = "READY_FOR_REVIEW"
            report.summary_json = {"helmet_violations": sum(item.type == "HELMET_VIOLATION" for item in recent.values()), "potholes": sum(item.type == "POTHOLE" for item in recent.values())}
            _set_progress(report, read=metadata.frame_count, stage="Ready for human verification", percent=100, timestamp=metadata.duration)
            database.commit()
    except (ModelLoadError, VideoOpenError, OSError, ValueError) as exc:
        database.rollback()
        report = database.get(Report, report_id)
        if report is not None:
            report.status, report.processing_error = "FAILED", str(exc)
            _set_progress(report, read=0, stage="Failed", percent=0)
            database.commit()
        logger.exception("Analysis failed for report %s", report_id)
    except Exception:
        database.rollback()
        report = database.get(Report, report_id)
        if report is not None:
            report.status, report.processing_error = "FAILED", "Analysis failed unexpectedly; inspect backend logs."
            _set_progress(report, read=0, stage="Failed", percent=0)
            database.commit()
        logger.exception("Unexpected analysis failure for report %s", report_id)
    finally:
        database.close()
