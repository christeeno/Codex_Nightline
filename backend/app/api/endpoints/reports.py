"""Video upload and live processing-progress endpoints."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.reports import ProgressResponse, ReportResponse, VideoMetadataResponse
from app.services.orchestrator import ProcessingOrchestrator
from app.services.progress import progress_registry
from app.services.video_reader import VideoOpenError
from app.services.video_storage import UploadValidationError, VideoStorage


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()
orchestrator = ProcessingOrchestrator(
    storage=VideoStorage(
        upload_path=settings.upload_path,
        evidence_path=settings.evidence_path,
        max_size_mb=settings.max_upload_size_mb,
        extensions=settings.supported_extensions,
    ),
    traffic_fps=settings.traffic_fps,
    road_fps=settings.road_fps,
)


def _response(report_id: str, report_status: str, report: object) -> ReportResponse:
    return ReportResponse(
        id=report_id,
        status=report_status,
        metadata=VideoMetadataResponse(
            filename=report.filename,  # type: ignore[attr-defined]
            resolution=report.resolution,  # type: ignore[attr-defined]
            fps=report.fps,  # type: ignore[attr-defined]
            frame_count=report.frame_count,  # type: ignore[attr-defined]
            duration=report.duration,  # type: ignore[attr-defined]
            codec=report.codec,  # type: ignore[attr-defined]
        ),
    )


@router.post("/upload", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def upload_report_video(
    video: UploadFile = File(..., description="MP4, MOV, or AVI video"),
    database: Session = Depends(get_db),
) -> ReportResponse:
    """Store, validate, and synchronously sample an uploaded video."""
    try:
        video_path = await orchestrator.storage.save(video)
        report = orchestrator.create_report(database, video_path, video.filename or video_path.name)
        await run_in_threadpool(orchestrator.process, database, report)
        return _response(report.id, report.status, report)
    except (UploadValidationError, VideoOpenError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except Exception as error:
        logger.exception("Upload pipeline failed", extra={"event": "upload_pipeline_failed"})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Video processing failed.") from error


@router.get("/{report_id}/progress", response_model=ProgressResponse)
def get_report_progress(report_id: str) -> ProgressResponse:
    """Return live, process-local state for the current video pipeline run."""
    progress = progress_registry.get(report_id)
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report progress was not found.")
    return progress
