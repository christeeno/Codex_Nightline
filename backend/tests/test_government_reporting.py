from datetime import datetime, timezone
import json

import httpx

from app.core.config import Settings
from app.api.endpoints.workflow import mock_government_report
from app.models.report import Incident, Report
from app.services.government_reporting import GovernmentReporter, GovernmentReportingError, MockGovernmentReporter


def _report() -> Report:
    return Report(
        id="report-1",
        filename="drive.mp4",
        video_path="uploads/videos/drive.mp4",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _incident() -> Incident:
    return Incident(
        id="incident-1",
        report_id="report-1",
        type="POTHOLE",
        title="Road Surface Pothole",
        timestamp=12.5,
        frame_number=375,
        confidence=0.91,
        status="APPROVED",
    )


def test_submission_posts_verified_incidents_and_uses_authority_receipt() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("Authorization")
        seen["payload"] = json.loads(request.content)
        return httpx.Response(201, json={"tracking_id": "AUTH-2026-99", "message": "Received"})

    reporter = GovernmentReporter(
        Settings(
            government_submission_url="https://authority.example/reports",
            government_submission_api_token="secret",
            government_include_evidence_images=False,
        ),
        transport=httpx.MockTransport(handler),
    )

    receipt = reporter.submit(_report(), [_incident()])

    assert receipt.tracking_id == "AUTH-2026-99"
    assert receipt.message == "Received"
    assert seen["authorization"] == "Bearer secret"
    assert seen["payload"]["incidents"][0]["incident_id"] == "incident-1"


def test_mock_report_contains_issue_time_place_and_number_plate() -> None:
    incident = _incident()
    incident.license_plate = "MH 01 AB 1234"
    incident.details = {"location": "MG Road, Pune"}

    receipt = MockGovernmentReporter().submit(_report(), [incident])

    assert receipt.delivery_mode == "mock"
    assert "Issue: Road Surface Pothole" in receipt.report_text
    assert "Time in footage: 0:00:12" in receipt.report_text
    assert "Place: MG Road, Pune" in receipt.report_text
    assert "Number plate: MH 01 AB 1234" in receipt.report_text


def test_mock_government_api_accepts_a_written_report() -> None:
    response = mock_government_report(
        {"report_text": "Issue: pothole\nTime: 10:30\nPlace: MG Road\nNumber plate: MH 01 AB 1234"}
    )

    assert response["data"]["tracking_id"].startswith("MOCK-GOV-")
