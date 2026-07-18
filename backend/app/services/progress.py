"""Thread-safe, in-memory processing progress for the MVP."""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import Lock
from time import monotonic

from app.schemas.reports import ProgressResponse


@dataclass(frozen=True)
class ProcessingProgress:
    report_id: str
    frames_read: int
    frames_total: int
    current_timestamp: float
    current_stage: str
    status: str
    started_at: float
    updated_at: datetime
    error: str | None = None

    def as_response(self) -> ProgressResponse:
        elapsed = max(monotonic() - self.started_at, 0.0)
        percent = 100.0 if self.frames_total == 0 else min(100.0, self.frames_read / self.frames_total * 100)
        remaining = max(self.frames_total - self.frames_read, 0)
        eta = 0.0 if self.frames_read == 0 else elapsed / self.frames_read * remaining
        return ProgressResponse(
            report_id=self.report_id,
            frames_read=self.frames_read,
            frames_remaining=remaining,
            current_timestamp=self.current_timestamp,
            percent_complete=percent,
            estimated_time_remaining=eta,
            current_stage=self.current_stage,
            status=self.status,  # type: ignore[arg-type]
            updated_at=self.updated_at,
            error=self.error,
        )


class ProgressRegistry:
    """A process-local registry intentionally replacing a queue/Redis for the MVP."""

    def __init__(self) -> None:
        self._states: dict[str, ProcessingProgress] = {}
        self._lock = Lock()

    def start(self, report_id: str, frame_total: int) -> None:
        with self._lock:
            self._states[report_id] = ProcessingProgress(
                report_id=report_id,
                frames_read=0,
                frames_total=frame_total,
                current_timestamp=0.0,
                current_stage="metadata_extracted",
                status="uploaded",
                started_at=monotonic(),
                updated_at=datetime.now(timezone.utc),
            )

    def update(self, report_id: str, **changes: object) -> None:
        with self._lock:
            current = self._states.get(report_id)
            if current is None:
                raise KeyError(report_id)
            self._states[report_id] = replace(
                current, updated_at=datetime.now(timezone.utc), **changes
            )

    def get(self, report_id: str) -> ProgressResponse | None:
        with self._lock:
            state = self._states.get(report_id)
        return state.as_response() if state else None


progress_registry = ProgressRegistry()
