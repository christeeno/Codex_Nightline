"""Reusable streaming orchestrator used to validate video-processing behavior."""
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from sqlalchemy.orm import Session
from app.models.report import Report
from app.schemas.detections import DetectionBatch
from app.services.frame_sampling import FrameSampler
from app.services.progress import ProgressRegistry, progress_registry
from app.services.video_reader import VideoReader
from app.services.video_storage import VideoStorage
class ProcessingOrchestrator:
    def __init__(self, storage: VideoStorage, traffic_fps: float, road_fps: float, registry: ProgressRegistry = progress_registry): self.storage, self.traffic_fps, self.road_fps, self.registry = storage, traffic_fps, road_fps, registry
    def create_report(self, database: Session, video_path: str | Path, original_filename: str) -> Report:
        with VideoReader(video_path) as reader: metadata = reader.metadata
        report = Report(filename=original_filename, video_name=original_filename, video_path=str(video_path), status="PENDING", resolution=metadata.resolution, fps=metadata.fps, frame_count=metadata.frame_count, duration=metadata.duration, video_duration=metadata.duration, codec=metadata.codec)
        database.add(report); database.commit(); database.refresh(report); self.registry.start(report.id, metadata.frame_count); return report
    def process(self, database: Session, report: Report) -> DetectionBatch:
        started, sampled, traffic_next, road_next = monotonic(), 0, 0.0, 0.0; traffic, road = FrameSampler(self.traffic_fps), FrameSampler(self.road_fps)
        report.status = "PROCESSING"; database.commit(); self.registry.update(report.id, status="processing", current_stage="frame_sampling")
        with VideoReader(report.video_path) as reader:
            for frame in reader.frames():
                due, traffic_next = traffic.accepts(frame, traffic_next); sampled += int(due)
                due, road_next = road.accepts(frame, road_next); sampled += int(due)
                self.registry.update(report.id, frames_read=frame.frame_number + 1, current_timestamp=frame.timestamp)
        report.status, report.completed_at = "READY_FOR_REVIEW", datetime.now(timezone.utc); database.commit(); self.registry.update(report.id, status="completed", current_stage="completed", frames_read=report.frame_count or 0, current_timestamp=report.duration or 0)
        return DetectionBatch(detections=[], processing_time=monotonic() - started, frames_processed=sampled, video_duration=report.duration or 0)
