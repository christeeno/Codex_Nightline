"""Synchronous video processing coordinator and future engine integration point."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

from sqlalchemy.orm import Session

from app.models.report import Report
from app.schemas.detections import Detection as PipelineDetection
from app.schemas.detections import DetectionBatch
from app.schemas.reports import VideoMetadataResponse
from app.services.frame_sampling import FrameSampler
from app.services.progress import ProgressRegistry, progress_registry
from app.services.road_intelligence import RoadIntelligenceEngine, SampledFrame
from app.services.video_reader import VideoMetadata, VideoOpenError, VideoReader
from app.services.video_storage import VideoStorage


logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """Inspect, sample, and track a video without loading it all into memory."""

    def __init__(
        self,
        storage: VideoStorage,
        traffic_fps: float,
        road_fps: float,
        registry: ProgressRegistry = progress_registry,
        road_engine: RoadIntelligenceEngine | None = None,
    ):
        self.storage = storage
        self.traffic_fps = traffic_fps
        self.road_fps = road_fps
        self.registry = registry
        self.road_engine = road_engine

    @staticmethod
    def _metadata_response(metadata: VideoMetadata) -> VideoMetadataResponse:
        return VideoMetadataResponse(**metadata.__dict__)

    def create_report(self, database: Session, video_path: str | Path, original_filename: str) -> Report:
        """Validate a stored video, persist its metadata, and initialize progress."""
        try:
            with VideoReader(video_path) as reader:
                metadata = reader.metadata
        except VideoOpenError:
            Path(video_path).unlink(missing_ok=True)
            logger.exception("Invalid video rejected", extra={"event": "video_validation_failed"})
            raise

        report = Report(
            filename=original_filename,
            video_path=str(video_path),
            resolution=metadata.resolution,
            fps=metadata.fps,
            frame_count=metadata.frame_count,
            duration=metadata.duration,
            codec=metadata.codec,
            extra_metadata={"source_filename": original_filename},
        )
        database.add(report)
        database.commit()
        database.refresh(report)
        self.registry.start(report.id, metadata.frame_count)
        logger.info("Metadata extracted", extra={"event": "metadata_extracted", "report_id": report.id})
        return report

    def process(self, database: Session, report: Report) -> DetectionBatch:
        """Stream the video once and dispatch ROAD_FPS frames to the road engine."""
        started = monotonic()
        traffic_sampler, road_sampler = FrameSampler(self.traffic_fps), FrameSampler(self.road_fps)
        traffic_next = road_next = 0.0
        sampled_frames = 0
        try:
            report.status = "processing"
            database.commit()
            self.registry.update(report.id, status="processing", current_stage="frame_sampling")
            logger.info("Processing started", extra={"event": "processing_started", "report_id": report.id})
            with VideoReader(report.video_path) as reader:
                def road_frames():
                    nonlocal traffic_next, road_next, sampled_frames
                    for frame in reader.frames():
                        traffic_due, traffic_next = traffic_sampler.accepts(frame, traffic_next)
                        road_due, road_next = road_sampler.accepts(frame, road_next)
                        if traffic_due:
                            sampled_frames += 1  # Traffic Engine integration point.
                        if road_due:
                            sampled_frames += 1
                        self.registry.update(
                            report.id,
                            frames_read=frame.frame_number + 1,
                            current_timestamp=frame.timestamp,
                        )
                        if frame.frame_number and frame.frame_number % 100 == 0:
                            logger.info("Frames processed", extra={"event": "frames_processed", "report_id": report.id, "frames_read": frame.frame_number + 1})
                        if road_due:
                            yield SampledFrame(
                                image=frame.image,
                                frame_number=frame.frame_number,
                                timestamp=frame.timestamp,
                            )

                road_result = (
                    self.road_engine.analyze_video(report.video_path, road_frames())
                    if self.road_engine is not None
                    else None
                )
                if road_result is None:
                    # Preserve complete-video/progress behavior when inference is disabled.
                    for _ in road_frames():
                        pass

            report.status = "completed"
            report.completed_at = datetime.now(timezone.utc)
            database.commit()
            self.registry.update(
                report.id,
                status="completed",
                current_stage="completed",
                frames_read=report.frame_count or 0,
                current_timestamp=report.duration or 0.0,
            )
            self.storage.cleanup_temporary_evidence()
            logger.info("Processing completed", extra={"event": "processing_completed", "report_id": report.id})
            detections = []
            if road_result is not None:
                detections = [
                    PipelineDetection(
                        type=detection.type,
                        timestamp=detection.timestamp,
                        frame_number=detection.frame_number,
                        confidence=detection.confidence,
                        bounding_box=(
                            detection.bounding_box.x1,
                            detection.bounding_box.y1,
                            detection.bounding_box.x2,
                            detection.bounding_box.y2,
                        ),
                        tracking_id=detection.tracking_id,
                        metadata=detection.metadata,
                    )
                    for detection in road_result.detections
                ]
            return DetectionBatch(
                detections=detections,
                processing_time=monotonic() - started,
                frames_processed=sampled_frames,
                video_duration=report.duration or 0.0,
            )
        except Exception as error:
            database.rollback()
            report.status = "failed"
            report.processing_error = str(error)
            database.commit()
            self.registry.update(report.id, status="failed", current_stage="failed", error=str(error))
            logger.exception("Processing failed", extra={"event": "processing_failed", "report_id": report.id})
            raise
