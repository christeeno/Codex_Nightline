"""Production-facing endpoints for the complete PARA AI review workflow."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.report import Incident, Report, Submission
from app.services.report_processing import process_report
from app.services.video_reader import VideoOpenError, VideoReader
from app.services.video_storage import UploadValidationError, VideoStorage

router = APIRouter(tags=["PARA AI workflow"])
settings = get_settings()
storage = VideoStorage(
    upload_path=settings.upload_path,
    evidence_path=settings.evidence_path,
    max_size_mb=settings.max_upload_size_mb,
    extensions=settings.supported_extensions,
)


def _not_found(label: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{label} was not found.")


def _report_data(report: Report, include_incidents: bool = False) -> dict:
    data = {
        "id": report.id,
        "filename": report.filename,
        "status": report.status,
        "metadata": {
            "resolution": report.resolution,
            "fps": report.fps,
            "frame_count": report.frame_count,
            "duration": report.duration,
            "codec": report.codec,
        },
        "summary": report.summary_json or {},
        "created_at": report.created_at,
        "completed_at": report.completed_at,
        "tracking_id": report.tracking_id,
        "error": report.processing_error,
    }
    if include_incidents:
        data["incidents"] = [_incident_data(item) for item in report.incidents]
    return data


def _incident_data(incident: Incident) -> dict:
    return {
        "id": incident.id,
        "report_id": incident.report_id,
        "type": incident.type,
        "title": incident.title,
        "timestamp": incident.timestamp,
        "frame_number": incident.frame_number,
        "confidence": incident.confidence,
        "severity": incident.severity,
        "status": incident.status,
        "approved": incident.approved,
        "license_plate": incident.license_plate or settings.unknown_label,
        "ocr_confidence": incident.ocr_confidence or 0.0,
        "evidence_url": f"/uploads/{incident.evidence_path}" if incident.evidence_path else None,
        "reward_credits": incident.reward_credits,
        "details": incident.details or {},
    }


@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="Upload dashcam footage")
async def upload_video(
    video: UploadFile = File(..., description="MP4, MOV, or AVI dashcam video"),
    database: Session = Depends(get_db),
) -> dict:
    """Persist and validate a video; analysis begins only when explicitly requested."""
    try:
        saved = await storage.save(video)
        with VideoReader(saved) as reader:
            metadata = reader.metadata
        report = Report(
            filename=Path(video.filename or saved.name).name,
            video_name=Path(video.filename or saved.name).name,
            video_path=str(saved),
            status="PENDING",
            resolution=metadata.resolution,
            fps=metadata.fps,
            frame_count=metadata.frame_count,
            duration=metadata.duration,
            video_duration=metadata.duration,
            codec=metadata.codec,
            summary_json={"progress": {"percent_complete": 0, "current_stage": "Ready to analyze"}},
        )
        database.add(report)
        database.commit()
        database.refresh(report)
        return {"message": "Video uploaded successfully.", "data": _report_data(report)}
    except (UploadValidationError, VideoOpenError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not store the uploaded video.") from exc


@router.post("/analyze/{report_id}", status_code=status.HTTP_202_ACCEPTED, summary="Analyze an uploaded report")
def analyze_report(report_id: str, background_tasks: BackgroundTasks, database: Session = Depends(get_db)) -> dict:
    """Queue exactly one full-video analysis run for a previously uploaded report."""
    report = database.get(Report, report_id)
    if report is None:
        raise _not_found("Report")
    if report.status == "PROCESSING":
        raise HTTPException(status_code=409, detail="This report is already being analyzed.")
    if report.status == "SUBMITTED":
        raise HTTPException(status_code=409, detail="Submitted reports cannot be analyzed again.")
    report.status = "PROCESSING"
    report.processing_error = None
    report.summary_json = {"progress": {"percent_complete": 0, "current_stage": "Queued"}}
    database.commit()
    background_tasks.add_task(process_report, report.id)
    return {"message": "Analysis started.", "data": {"report_id": report.id, "status": report.status}}


@router.get("/reports", summary="List reports")
def list_reports(database: Session = Depends(get_db)) -> dict:
    reports = list(database.scalars(select(Report).order_by(Report.created_at.desc())))
    return {"message": "Reports retrieved successfully.", "data": [_report_data(item) for item in reports]}


@router.get("/reports/{report_id}", summary="Get report details")
def get_report(report_id: str, database: Session = Depends(get_db)) -> dict:
    report = database.get(Report, report_id)
    if report is None:
        raise _not_found("Report")
    return {"message": "Report retrieved successfully.", "data": _report_data(report, include_incidents=True)}


@router.get("/reports/{report_id}/progress", summary="Get processing progress")
def get_progress(report_id: str, database: Session = Depends(get_db)) -> dict:
    report = database.get(Report, report_id)
    if report is None:
        raise _not_found("Report")
    progress = (report.summary_json or {}).get("progress", {})
    return {"message": "Progress retrieved successfully.", "data": {
        "report_id": report.id,
        "status": report.status,
        "frames_read": progress.get("frames_read", 0),
        "frames_total": report.frame_count or 0,
        "current_timestamp": progress.get("current_timestamp", 0),
        "percent_complete": progress.get("percent_complete", 0),
        "current_stage": progress.get("current_stage", "Ready to analyze"),
        "error": report.processing_error,
    }}


@router.get("/reports/{report_id}/incidents", summary="List incidents for review")
def list_incidents(report_id: str, database: Session = Depends(get_db)) -> dict:
    report = database.get(Report, report_id)
    if report is None:
        raise _not_found("Report")
    incidents = list(database.scalars(select(Incident).where(Incident.report_id == report.id).order_by(Incident.timestamp)))
    return {"message": "Incidents retrieved successfully.", "data": [_incident_data(item) for item in incidents]}


def _review_incident(report_id: str, incident_id: str, approved: bool, database: Session) -> dict:
    incident = database.get(Incident, incident_id)
    if incident is None or incident.report_id != report_id:
        raise _not_found("Incident")
    if incident.status != "PENDING":
        raise HTTPException(status_code=409, detail="This incident has already been reviewed.")
    incident.status = "APPROVED" if approved else "REJECTED"
    incident.approved = approved
    database.commit()
    database.refresh(incident)
    return {"message": f"Incident {'approved' if approved else 'rejected'} successfully.", "data": _incident_data(incident)}


@router.post("/reports/{report_id}/incidents/{incident_id}/approve", summary="Approve an incident")
def approve_incident(report_id: str, incident_id: str, database: Session = Depends(get_db)) -> dict:
    return _review_incident(report_id, incident_id, True, database)


@router.post("/reports/{report_id}/incidents/{incident_id}/reject", summary="Reject an incident")
def reject_incident(report_id: str, incident_id: str, database: Session = Depends(get_db)) -> dict:
    return _review_incident(report_id, incident_id, False, database)


@router.post("/reports/{report_id}/submit", status_code=status.HTTP_201_CREATED, summary="Create mock government submission")
def submit_report(report_id: str, database: Session = Depends(get_db)) -> dict:
    report = database.get(Report, report_id)
    if report is None:
        raise _not_found("Report")
    if report.status not in {"READY_FOR_REVIEW", "SUBMITTED"}:
        raise HTTPException(status_code=409, detail="Finish analysis before submitting this report.")
    if report.tracking_id:
        return {"message": "Report was already submitted.", "data": {"report_id": report.id, "tracking_id": report.tracking_id, "status": "SUBMITTED"}}
    tracking_id = f"PARA-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:8].upper()}"
    submission = Submission(report_id=report.id, government_tracking_id=tracking_id, submission_status="SUBMITTED", response_json={"mock": True, "accepted_at": datetime.now(timezone.utc).isoformat()})
    report.status = "SUBMITTED"
    report.submission_status = "SUBMITTED"
    report.tracking_id = tracking_id
    report.submitted_at = datetime.now(timezone.utc)
    database.add(submission)
    database.commit()
    return {"message": "Mock government submission created.", "data": {"report_id": report.id, "tracking_id": tracking_id, "status": "SUBMITTED"}}


@router.get("/dashboard", summary="Get citizen dashboard totals")
def dashboard(database: Session = Depends(get_db)) -> dict:
    count = lambda statement: database.scalar(statement) or 0
    submitted = count(select(func.count()).select_from(Report).where(Report.status == "SUBMITTED"))
    pending = count(select(func.count()).select_from(Incident).where(Incident.status == "PENDING"))
    approved = count(select(func.count()).select_from(Incident).where(Incident.status == "APPROVED"))
    rejected = count(select(func.count()).select_from(Incident).where(Incident.status == "REJECTED"))
    rewards = count(select(func.coalesce(func.sum(Incident.reward_credits), 0)).where(Incident.status == "APPROVED"))
    return {"message": "Dashboard retrieved successfully.", "data": {"submitted": submitted, "verified": approved, "pending": pending, "rejected": rejected, "rewards": rewards}}
