"""Traffic-violation engine backed only by Bike-Helmet-Detectionv2."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import logging
from pathlib import Path
import time
from typing import Protocol

import numpy as np

from app.adapters.bike_helmet import BikeHelmetAdapter, HelmetViolationCandidate
from app.core.config import Settings, get_settings
from app.schemas.detection import BoundingBox, Detection, ProcessingStatistics, TrafficAnalysisResult


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrafficFrame:
    """One traffic-rate sample supplied by the existing video pipeline."""

    image: np.ndarray
    frame_number: int
    timestamp: float


class TrafficFrameSource(Protocol):
    """The orchestrator frame interface; this engine never opens a video itself."""

    def iter_traffic_frames(self, video_path: Path, fps: int) -> Iterator[TrafficFrame]: ...


class TrafficViolationEngine:
    """Analyze all orchestrator traffic frames and normalize helmet violations.

    Bike-Helmet-Detectionv2 has no documented triple-riding output. The engine
    therefore returns no such detections instead of inferring or fabricating it.
    """

    def __init__(
        self,
        frame_source: TrafficFrameSource | None = None,
        adapter: BikeHelmetAdapter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._frame_source = frame_source
        self._adapter = adapter or BikeHelmetAdapter(self._settings)
        self._temporary_tracks: dict[str, BoundingBox] = {}
        self._next_tracking_id = 1

    def analyze_video(
        self,
        video_path: str | Path,
        frames: Iterable[TrafficFrame] | None = None,
    ) -> TrafficAnalysisResult:
        """Process the complete supplied stream and never raise inference errors."""
        started = time.perf_counter()
        video = Path(video_path)
        stats = ProcessingStatistics(video_path=str(video))
        detections: list[Detection] = []
        logger.info("Inference started engine=traffic video=%s fps=%s", video, self._settings.traffic_fps)

        try:
            frame_stream = frames if frames is not None else self._pipeline_frames(video)
            for frame in frame_stream:
                stats.frames_processed += 1
                if not _valid_frame(frame.image):
                    logger.warning("Traffic inference skipped invalid frame=%s", frame.frame_number)
                    continue
                candidates = self._adapter.detect(frame.image)
                stats.candidate_detections += len(candidates)
                for candidate in candidates:
                    detection = self._detection_from_candidate(candidate, frame)
                    detections.append(detection)
                    logger.info(
                        "Violation detected type=%s frame=%s tracking_id=%s confidence=%.3f",
                        detection.type,
                        frame.frame_number,
                        detection.tracking_id,
                        detection.confidence,
                    )
        except Exception as exc:  # noqa: BLE001 - corrupted pipeline input must not crash backend
            message = f"Traffic violation processing failed: {exc}"
            logger.exception(message)
            stats.errors.append(message)

        elapsed = time.perf_counter() - started
        stats.helmet_violations = len(detections)
        # The upstream repository documents bike/rider/helmet classes only.
        stats.triple_riding_violations = 0
        stats.inference_seconds = round(elapsed, 4)
        stats.average_fps = round(stats.frames_processed / elapsed, 3) if elapsed else 0.0
        logger.info("Frames processed engine=traffic count=%s", stats.frames_processed)
        logger.info("Violations detected engine=traffic count=%s", stats.helmet_violations)
        logger.info("Inference time engine=traffic seconds=%.4f", elapsed)
        logger.info("Average FPS engine=traffic value=%.3f", stats.average_fps)
        logger.info("Processing completed engine=traffic video=%s", video)
        return TrafficAnalysisResult(detections=detections, statistics=stats)

    def _pipeline_frames(self, video_path: Path) -> Iterator[TrafficFrame]:
        if self._frame_source is None:
            raise RuntimeError("No Processing Pipeline TrafficFrameSource is configured")
        return self._frame_source.iter_traffic_frames(video_path, self._settings.traffic_fps)

    def _detection_from_candidate(self, candidate: HelmetViolationCandidate, frame: TrafficFrame) -> Detection:
        tracking_id = candidate.tracking_id or self._temporary_tracking_id(candidate.bounding_box)
        return Detection(
            type="HELMET_VIOLATION",
            timestamp=frame.timestamp,
            frame_number=frame.frame_number,
            confidence=candidate.confidence,
            bounding_box=candidate.bounding_box,
            tracking_id=tracking_id,
            metadata={
                "source": BikeHelmetAdapter.source_name,
                "source_label": candidate.source_label,
                "rider_bounding_box": candidate.rider_box.model_dump(),
                "motorcycle_bounding_box": candidate.motorcycle_box.model_dump(),
            },
        )

    def _temporary_tracking_id(self, bounding_box: BoundingBox) -> str:
        for tracking_id, previous_box in self._temporary_tracks.items():
            if _iou(previous_box, bounding_box) >= self._settings.traffic_tracking_iou:
                self._temporary_tracks[tracking_id] = bounding_box
                return tracking_id
        tracking_id = f"traffic-{self._next_tracking_id:06d}"
        self._next_tracking_id += 1
        self._temporary_tracks[tracking_id] = bounding_box
        return tracking_id


def _valid_frame(image: np.ndarray) -> bool:
    return isinstance(image, np.ndarray) and image.ndim >= 2 and image.size > 0


def _iou(first: BoundingBox, second: BoundingBox) -> float:
    left, top = max(first.x1, second.x1), max(first.y1, second.y1)
    right, bottom = min(first.x2, second.x2), min(first.y2, second.y2)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    union = first.area + second.area - intersection
    return intersection / union if union else 0.0
