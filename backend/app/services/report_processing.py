"""Small, synchronous processing pipeline used by the API background task.

Model adapters can replace ``_demo_candidates`` without changing API contracts.  The
demo candidate generator is deliberately opt-in through settings and makes the
hackathon flow demonstrable when vendor weights are not present locally.
"""

from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.report import Incident, Report
from app.services.video_reader import VideoOpenError, VideoReader


def _progress(report: Report, *, frames_read: int, stage: str, status: str, error: str | None = None) -> None:
    metadata = dict(report.extra_metadata or {})
    metadata["progress"] = {
        "frames_read": frames_read,
        "current_stage": stage,
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }
    report.extra_metadata = metadata


def _demo_candidates(duration: float, frame_count: int) -> list[dict]:
    """Provide clearly labelled, deduplicated demo evidence when no weights exist."""
    points = [max(0.5, duration * 0.32), max(1.0, duration * 0.68)]
    return [
        {
            "type": "helmet_violation",
            "title": "Missing Helmet Detection",
            "timestamp": points[0],
            "frame_number": min(frame_count - 1, max(0, int(frame_count * 0.32))),
            "confidence": 0.91,
            "license_plate": "DEMO-2048",
            "ocr_confidence": 0.86,
            "reward": 150,
        },
        {
            "type": "pothole",
            "title": "Road Surface Pothole",
            "timestamp": points[1],
            "frame_number": min(frame_count - 1, max(0, int(frame_count * 0.68))),
            "confidence": 0.84,
            "license_plate": None,
            "ocr_confidence": None,
            "reward": 80,
        },
    ]


def _write_evidence(image: object, report_id: str, timestamp: float) -> str | None:
    """Persist one representative frame. Failure to write evidence is non-fatal."""
    try:
        import cv2

        settings = get_settings()
        name = f"{report_id}-{timestamp:.2f}.jpg"
        target = Path(settings.evidence_path) / name
        if cv2.imwrite(str(target), image):
            return f"evidence/{name}"
    except Exception:
        return None
    return None


def process_report(report_id: str) -> None:
    """Analyze one report and persist progress, incidents, and useful failures."""
    database: Session = SessionLocal()
    started = monotonic()
    try:
        report = database.get(Report, report_id)
        if report is None:
            return
        report.status = "processing"
        _progress(report, frames_read=0, stage="Loading video", status="processing")
        database.commit()

        with VideoReader(report.video_path) as reader:
            metadata = reader.metadata
            report.fps = metadata.fps
            report.frame_count = metadata.frame_count
            report.duration = metadata.duration
            report.resolution = metadata.resolution
            report.codec = metadata.codec
            candidates = _demo_candidates(metadata.duration, metadata.frame_count) if get_settings().demo_inference else []
            candidate_index = 0
            last_image = None
            for frame in reader.frames():
                last_image = frame.image
                if candidate_index < len(candidates) and frame.frame_number >= candidates[candidate_index]["frame_number"]:
                    item = candidates[candidate_index]
                    evidence_path = _write_evidence(frame.image, report.id, item["timestamp"])
                    database.add(Incident(
                        report_id=report.id,
                        type=item["type"],
                        title=item["title"],
                        timestamp=item["timestamp"],
                        frame_number=item["frame_number"],
                        confidence=item["confidence"],
                        license_plate=item["license_plate"],
                        ocr_confidence=item["ocr_confidence"],
                        evidence_path=evidence_path,
                        reward_credits=item["reward"],
                        details={"source": "demo_inference", "ocr_attempted": item["license_plate"] is not None},
                    ))
                    candidate_index += 1
                if frame.frame_number % max(1, int(metadata.fps)) == 0:
                    percent = frame.frame_number / max(1, metadata.frame_count)
                    stage = "Traffic and OCR analysis" if percent < 0.6 else "Road integrity analysis"
                    _progress(report, frames_read=frame.frame_number, stage=stage, status="processing")
                    database.commit()
            if candidates and candidate_index < len(candidates) and last_image is not None:
                # Very short videos still yield unique demo events.
                for item in candidates[candidate_index:]:
                    database.add(Incident(report_id=report.id, type=item["type"], title=item["title"], timestamp=item["timestamp"], frame_number=item["frame_number"], confidence=item["confidence"], license_plate=item["license_plate"], ocr_confidence=item["ocr_confidence"], evidence_path=_write_evidence(last_image, report.id, item["timestamp"]), reward_credits=item["reward"], details={"source": "demo_inference", "ocr_attempted": item["license_plate"] is not None}))
            report.status = "completed"
            report.completed_at = datetime.now(timezone.utc)
            _progress(report, frames_read=metadata.frame_count, stage="Complete", status="completed")
            database.commit()
    except (VideoOpenError, OSError, ValueError) as exc:
        database.rollback()
        report = database.get(Report, report_id)
        if report is not None:
            report.status = "failed"
            report.processing_error = str(exc)
            _progress(report, frames_read=0, stage="Failed", status="failed", error=str(exc))
            database.commit()
    except Exception as exc:  # pragma: no cover - defensive persistence boundary
        database.rollback()
        report = database.get(Report, report_id)
        if report is not None:
            report.status = "failed"
            report.processing_error = "Processing failed unexpectedly. Check backend logs."
            _progress(report, frames_read=0, stage="Failed", status="failed", error=report.processing_error)
            database.commit()
    finally:
        database.close()
