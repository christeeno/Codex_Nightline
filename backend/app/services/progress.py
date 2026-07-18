"""Thread-safe progress snapshots for streaming analysis."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
@dataclass(frozen=True)
class ProgressResponse:
    report_id: str; frames_read: int; frames_remaining: int; current_timestamp: float; percent_complete: float; estimated_time_remaining: float; current_stage: str; status: str; updated_at: datetime; error: str | None = None
@dataclass(frozen=True)
class _Progress:
    report_id: str; frames_read: int; frames_total: int; current_timestamp: float; current_stage: str; status: str; started_at: float; updated_at: datetime; error: str | None = None
    def response(self):
        elapsed = max(monotonic() - self.started_at, 0); remaining = max(self.frames_total - self.frames_read, 0); percent = 100.0 if not self.frames_total else min(100.0, self.frames_read / self.frames_total * 100)
        return ProgressResponse(self.report_id, self.frames_read, remaining, self.current_timestamp, percent, 0 if not self.frames_read else elapsed / self.frames_read * remaining, self.current_stage, self.status, self.updated_at, self.error)
class ProgressRegistry:
    def __init__(self): self._items, self._lock = {}, Lock()
    def start(self, report_id, frame_total):
        with self._lock: self._items[report_id] = _Progress(report_id, 0, frame_total, 0, "metadata_extracted", "uploaded", monotonic(), datetime.now(timezone.utc))
    def update(self, report_id, **values):
        with self._lock: self._items[report_id] = replace(self._items[report_id], updated_at=datetime.now(timezone.utc), **values)
    def get(self, report_id):
        with self._lock: item = self._items.get(report_id)
        return item.response() if item else None
progress_registry = ProgressRegistry()
