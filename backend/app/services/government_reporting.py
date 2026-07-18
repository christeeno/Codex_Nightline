"""Delivery adapter for a configured government reporting endpoint.

The receiving authority owns the endpoint and credentials.  This adapter uses
a small, documented JSON envelope so deployments can connect it to an agency
API or an integration gateway without pretending that a local database record
is a government receipt.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from app.core.config import Settings
from app.models.report import Incident, Report


class GovernmentReportingError(RuntimeError):
    """Raised when a verified report cannot be delivered to the authority."""


@dataclass(frozen=True)
class GovernmentReceipt:
    tracking_id: str | None
    message: str
    response: dict[str, Any]
    delivery_mode: str = "government"
    report_text: str | None = None


class GovernmentReporter:
    """Send approved incidents to the authority configured for this deployment."""

    def __init__(self, settings: Settings, *, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    def submit(self, report: Report, incidents: list[Incident]) -> GovernmentReceipt:
        if not self.settings.government_submission_url:
            raise GovernmentReportingError(
                "Government reporting is not configured. Set GOVERNMENT_SUBMISSION_URL "
                "and any required GOVERNMENT_SUBMISSION_API_TOKEN; no report was sent."
            )

        headers = {"Accept": "application/json"}
        if self.settings.government_submission_api_token:
            headers["Authorization"] = f"Bearer {self.settings.government_submission_api_token}"

        try:
            with httpx.Client(
                timeout=self.settings.government_submission_timeout_seconds,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.post(
                    self.settings.government_submission_url,
                    headers=headers,
                    json=self._payload(report, incidents),
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GovernmentReportingError(
                f"{self.settings.government_authority_name} rejected the report "
                f"(HTTP {exc.response.status_code})."
            ) from exc
        except httpx.HTTPError as exc:
            raise GovernmentReportingError(
                f"Could not deliver the report to {self.settings.government_authority_name}."
            ) from exc

        try:
            response_data = response.json()
        except ValueError:
            response_data = {"body": response.text[:1000]}
        if not isinstance(response_data, dict):
            response_data = {"body": response_data}
        receipt = response_data.get("data", response_data)
        if not isinstance(receipt, dict):
            receipt = response_data
        tracking_id = self._first_text(receipt, "tracking_id", "trackingId", "reference", "reference_number", "id")
        message = self._first_text(receipt, "message", "status_message") or (
            f"Accepted by {self.settings.government_authority_name}."
        )
        return GovernmentReceipt(tracking_id=tracking_id, message=message, response=response_data)

    def _payload(self, report: Report, incidents: list[Incident]) -> dict[str, Any]:
        return {
            "source": "PARA AI",
            "report_id": report.id,
            "created_at": report.created_at.isoformat(),
            "video": {
                "filename": report.filename,
                "duration_seconds": report.duration,
                "resolution": report.resolution,
            },
            "incidents": [self._incident_payload(incident) for incident in incidents],
        }

    def _incident_payload(self, incident: Incident) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "incident_id": incident.id,
            "type": incident.type,
            "title": incident.title,
            "timestamp_seconds": incident.timestamp,
            "frame_number": incident.frame_number,
            "confidence": incident.confidence,
            "severity": incident.severity,
            "license_plate": incident.license_plate,
            "ocr_confidence": incident.ocr_confidence,
            "details": incident.details or {},
        }
        if self.settings.government_include_evidence_images and incident.evidence_path:
            path = Path(self.settings.upload_folder) / incident.evidence_path
            if path.is_file():
                payload["evidence"] = {
                    "filename": path.name,
                    "content_type": "image/jpeg",
                    "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
                }
        return payload

    @staticmethod
    def _first_text(data: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            value = data.get(key)
            if isinstance(value, (str, int)) and str(value).strip():
                return str(value)
        return None


class MockGovernmentReporter:
    """Creates a clearly marked, send-ready report for local demos and review."""

    authority_name = "Mock Road Safety Authority"

    def submit(self, report: Report, incidents: list[Incident]) -> GovernmentReceipt:
        reference = f"MOCK-GOV-{uuid4().hex[:8].upper()}"
        report_text = self._report_text(report, incidents, reference)
        return GovernmentReceipt(
            tracking_id=reference,
            message="Mock report created. It has not been sent to a government authority.",
            response={
                "tracking_id": reference,
                "status": "PREPARED",
                "authority": self.authority_name,
                "report_text": report_text,
            },
            delivery_mode="mock",
            report_text=report_text,
        )

    @staticmethod
    def _report_text(report: Report, incidents: list[Incident], reference: str) -> str:
        lines = [
            f"To: {MockGovernmentReporter.authority_name}",
            "Subject: Road-safety incident report",
            f"Reference: {reference}",
            f"Report created: {report.created_at.astimezone().strftime('%d %b %Y, %H:%M %Z')}",
            f"Source video: {report.filename}",
            "",
            "Please investigate the following verified road-safety issue(s):",
        ]
        for number, incident in enumerate(incidents, start=1):
            footage_time = str(timedelta(seconds=round(incident.timestamp)))
            details = incident.details or {}
            place = details.get("location") or details.get("place") or "Location not provided in dashcam metadata"
            plate = incident.license_plate or "Number plate not visible"
            lines.extend([
                "",
                f"{number}. Issue: {incident.title} ({incident.type})",
                f"   Time in footage: {footage_time}",
                f"   Place: {place}",
                f"   Number plate: {plate}",
                f"   Evidence frame: {incident.frame_number}; confidence: {incident.confidence:.0%}",
            ])
        lines.extend([
            "",
            "Supporting evidence is retained with the PARA AI report.",
            "This mock document is prepared for manual submission and is not an official filing.",
        ])
        return "\n".join(lines)
