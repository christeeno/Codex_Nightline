"""Closed value sets used by PARA AI persistence and API contracts."""
from enum import Enum


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"


class IncidentType(str, Enum):
    HELMET_VIOLATION = "HELMET_VIOLATION"
    TRIPLE_RIDING = "TRIPLE_RIDING"
    POTHOLE = "POTHOLE"


class IncidentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SubmissionStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"
