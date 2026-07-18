"""Reusable CRUD operations; this module deliberately contains no AI logic."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Evidence, Incident, Report, Submission


def _apply_changes(instance: Any, values: dict[str, Any]) -> None:
    for name, value in values.items():
        if value is not None and hasattr(instance, name):
            setattr(instance, name, value)


def create_report(session: Session, values: dict[str, Any]) -> Report:
    data = dict(values)
    # These aliases preserve compatibility with the pre-existing upload model.
    data.setdefault("filename", data.get("video_name"))
    data.setdefault("duration", data.get("video_duration"))
    report = Report(**data)
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def update_report(session: Session, report: Report, values: dict[str, Any]) -> Report:
    _apply_changes(report, values)
    report.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(report)
    return report


def get_report(session: Session, report_id: UUID | str) -> Optional[Report]:
    return session.get(Report, str(report_id))


def list_reports(session: Session, offset: int = 0, limit: int = 100) -> list[Report]:
    statement = select(Report).order_by(Report.created_at.desc()).offset(offset).limit(limit)
    return list(session.scalars(statement))


def create_incident(session: Session, values: dict[str, Any]) -> Incident:
    incident = Incident(**values)
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


def update_incident(session: Session, incident: Incident, values: dict[str, Any]) -> Incident:
    _apply_changes(incident, values)
    session.commit()
    session.refresh(incident)
    return incident


def get_incident(session: Session, incident_id: UUID | str) -> Optional[Incident]:
    return session.get(Incident, str(incident_id))


def create_evidence(session: Session, values: dict[str, Any]) -> Evidence:
    evidence = Evidence(**values)
    session.add(evidence)
    session.commit()
    session.refresh(evidence)
    return evidence


def create_submission(session: Session, values: dict[str, Any]) -> Submission:
    submission = Submission(**values)
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return submission
