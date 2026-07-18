"""Stable REST interface for reports, review decisions, and dashboard data."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app import crud
from app.api.dependencies import LoggerDep, SessionDep, SettingsDep
from app.models import Incident, IncidentStatus, Report, ReportStatus, SubmissionStatus
from app.schemas.contracts import AnalyzeVideoRequest, ApiResponse, ApproveIncidentRequest, DashboardSummaryResponse, IncidentResponse, ProgressResponse, RecentActivityResponse, RejectIncidentRequest, ReportResponse, SubmissionResponse, SubmitReportRequest, UploadResponse, UploadVideoRequest

router = APIRouter(tags=["Reports"])


def _not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def _report_or_404(session: SessionDep, report_id: UUID) -> Report:
    report = crud.get_report(session, report_id)
    if report is None:
        raise _not_found("Report")
    return report


def _incident_or_404(session: SessionDep, report_id: UUID, incident_id: UUID) -> Incident:
    incident = crud.get_incident(session, incident_id)
    if incident is None or incident.report_id != str(report_id):
        raise _not_found("Incident")
    return incident


@router.post("/upload", response_model=ApiResponse[UploadResponse], status_code=status.HTTP_201_CREATED, summary="Register an uploaded dashcam video", description="Creates a pending report from video metadata. Binary file storage is outside this interface.")
def upload_video(payload: UploadVideoRequest, session: SessionDep, logger: LoggerDep, settings: SettingsDep):
    report = crud.create_report(session, {**payload.model_dump(), "status": ReportStatus.PENDING.value})
    logger.info("Registered report %s for %s", report.id, settings.app_name)
    return ApiResponse(message="Video registered successfully", data=UploadResponse(report_id=report.id, filename=report.video_name or report.filename, duration=report.video_duration, status=ReportStatus(report.status)))


@router.post("/analyze/{report_id}", response_model=ApiResponse[ProgressResponse], summary="Queue a report for analysis", description="Defines the asynchronous-analysis contract only; no processing is started yet.")
def analyze_video(report_id: UUID, payload: AnalyzeVideoRequest, session: SessionDep, logger: LoggerDep, settings: SettingsDep):
    report = _report_or_404(session, report_id)
    logger.info("Analysis requested for report %s (force=%s, app=%s)", report.id, payload.force, settings.app_name)
    return ApiResponse(message="Analysis request accepted; processing is not implemented yet", data=ProgressResponse(report_id=report.id, status=ReportStatus(report.status), progress_percent=0, message="Awaiting analysis implementation"))


@router.get("/reports", response_model=ApiResponse[list[ReportResponse]], summary="List reports", description="Returns stored reports ordered from newest to oldest.")
def list_report_records(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    return ApiResponse(message="Reports retrieved successfully", data=crud.list_reports(session, offset, limit))


@router.get("/reports/{report_id}", response_model=ApiResponse[ReportResponse], summary="Get report details", description="Returns a report with incidents and submission records.")
def get_report_record(report_id: UUID, session: SessionDep):
    return ApiResponse(message="Report retrieved successfully", data=_report_or_404(session, report_id))


@router.get("/reports/{report_id}/progress", response_model=ApiResponse[ProgressResponse], summary="Get report processing progress", description="Returns a fixed placeholder until the processing worker is introduced.")
def get_report_progress(report_id: UUID, session: SessionDep):
    report = _report_or_404(session, report_id)
    report_status = ReportStatus(report.status)
    progress = 100 if report_status in {ReportStatus.READY_FOR_REVIEW, ReportStatus.SUBMITTED} else 0
    return ApiResponse(message="Report progress retrieved successfully", data=ProgressResponse(report_id=report.id, status=report_status, progress_percent=progress, message="Processing is not implemented yet"))


@router.get("/reports/{report_id}/incidents", response_model=ApiResponse[list[IncidentResponse]], summary="List report incidents", description="Returns incidents persisted for one report.")
def list_report_incidents(report_id: UUID, session: SessionDep):
    _report_or_404(session, report_id)
    return ApiResponse(message="Incidents retrieved successfully", data=list(session.scalars(select(Incident).where(Incident.report_id == str(report_id)))))


@router.post("/reports/{report_id}/incidents/{incident_id}/approve", response_model=ApiResponse[IncidentResponse], summary="Approve an incident", description="Persists a reviewer decision only; it does not run downstream logic.")
def approve_incident(report_id: UUID, incident_id: UUID, payload: ApproveIncidentRequest, session: SessionDep):
    _report_or_404(session, report_id)
    incident = _incident_or_404(session, report_id, incident_id)
    return ApiResponse(message="Incident approved successfully", data=crud.update_incident(session, incident, {"status": IncidentStatus.APPROVED.value, "approved": True, "tracking_object": payload.tracking_object}))


@router.post("/reports/{report_id}/incidents/{incident_id}/reject", response_model=ApiResponse[IncidentResponse], summary="Reject an incident", description="Persists a reviewer rejection; the optional reason is not stored yet.")
def reject_incident(report_id: UUID, incident_id: UUID, payload: RejectIncidentRequest, session: SessionDep):
    _report_or_404(session, report_id)
    incident = _incident_or_404(session, report_id, incident_id)
    return ApiResponse(message="Incident rejected successfully", data=crud.update_incident(session, incident, {"status": IncidentStatus.REJECTED.value, "approved": False}))


@router.post("/reports/{report_id}/submit", response_model=ApiResponse[SubmissionResponse], status_code=status.HTTP_201_CREATED, summary="Create a mock government submission", description="Creates a local mock record only; no government service is contacted.")
def submit_report(report_id: UUID, payload: SubmitReportRequest, session: SessionDep):
    report = _report_or_404(session, report_id)
    submission = crud.create_submission(session, {"report_id": report.id, "government_tracking_id": payload.government_tracking_id, "submission_status": SubmissionStatus.SUBMITTED.value, "response_json": {"mock": True}})
    crud.update_report(session, report, {"status": ReportStatus.SUBMITTED.value, "submission_status": SubmissionStatus.SUBMITTED.value})
    return ApiResponse(message="Mock submission created successfully", data=submission)


@router.get("/dashboard", response_model=ApiResponse[DashboardSummaryResponse], tags=["Dashboard"], summary="Get dashboard summary", description="Returns stored aggregate counts and placeholder reward values.")
def get_dashboard(session: SessionDep):
    submitted = session.scalar(select(func.count()).select_from(Report).where(Report.submission_status == SubmissionStatus.SUBMITTED.value)) or 0
    pending = session.scalar(select(func.count()).select_from(Report).where(Report.status.in_([ReportStatus.PENDING.value, ReportStatus.PROCESSING.value]))) or 0
    rejected = session.scalar(select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.REJECTED.value)) or 0
    verified = session.scalar(select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.APPROVED.value)) or 0
    activity = [RecentActivityResponse(report_id=row.id, video_name=row.video_name or row.filename, status=ReportStatus(row.status), created_at=row.created_at) for row in crud.list_reports(session, 0, 5)]
    return ApiResponse(message="Dashboard summary retrieved successfully", data=DashboardSummaryResponse(reports_submitted=submitted, verified_reports=verified, pending_reports=pending, rejected_reports=rejected, rewards_earned=0, recent_activity=activity))
