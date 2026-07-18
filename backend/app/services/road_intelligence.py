"""Road Intelligence Engine for confirmed pothole detections only."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np

from app.adapters import PotholeDetectionAdapter
from app.core.config import Settings, get_settings
from app.schemas import BoundingBox, Detection, ProcessingStatistics, RoadAnalysisResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SampledFrame:
    """A frame supplied by the existing video processing pipeline."""

    image: np.ndarray
    frame_number: int
    timestamp: float
    vehicle_boxes: tuple[BoundingBox, ...] = ()


class FrameSource(Protocol):
    """Contract implemented by the Thread 3 processing pipeline."""

    def iter_sampled_frames(self, video_path: Path, fps: int) -> Iterator[SampledFrame]:
        """Yield every ROAD_FPS-sampled frame for a complete video."""


@dataclass
class _Candidate:
    bounding_box: BoundingBox
    confidence: float
    sampled_index: int
    frame_number: int
    timestamp: float
    blur_score: float
    image_shape: tuple[int, int]


@dataclass
class _PotholeEvent:
    candidates: list[_Candidate] = field(default_factory=list)
    last_sampled_index: int = -1


class RoadIntelligenceEngine:
    """Analyze pipeline frames and return high-precision pothole incidents.

    Frame decoding belongs to the existing Processing Pipeline.  Pass its
    ``FrameSource`` implementation at construction (or per request) so this
    engine never duplicates the pipeline's OpenCV extraction logic.
    """

    def __init__(
        self,
        frame_source: FrameSource | None = None,
        adapter: PotholeDetectionAdapter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._frame_source = frame_source
        self._adapter = adapter or PotholeDetectionAdapter(self._settings)

    def analyze_video(
        self,
        video_path: str | Path,
        frames: Iterable[SampledFrame] | None = None,
    ) -> RoadAnalysisResult:
        """Analyze all sampled frames and return non-fatal standardized results."""
        started = time.perf_counter()
        video = Path(video_path)
        stats = ProcessingStatistics(video_path=str(video))
        candidates: list[_Candidate] = []
        logger.info("Inference Started video=%s road_fps=%s", video, self._settings.road_fps)

        try:
            frame_stream = frames if frames is not None else self._pipeline_frames(video)
            for sampled_index, frame in enumerate(frame_stream):
                stats.frames_processed += 1
                if not self._valid_frame(frame.image):
                    logger.warning("Skipping invalid sampled frame frame=%s", frame.frame_number)
                    continue
                for box, confidence in self._adapter.detect(frame.image):
                    if not self._passes_precision_filters(box, frame):
                        continue
                    candidates.append(
                        _Candidate(
                            bounding_box=box,
                            confidence=confidence,
                            sampled_index=sampled_index,
                            frame_number=frame.frame_number,
                            timestamp=frame.timestamp,
                            blur_score=_sharpness(frame.image, box),
                            image_shape=frame.image.shape[:2],
                        )
                    )
        except Exception as exc:  # noqa: BLE001 - invalid video/pipeline failures are non-fatal
            message = f"Road intelligence processing failed: {exc}"
            logger.exception(message)
            stats.errors.append(message)

        stats.candidate_detections = len(candidates)
        events = self._confirmed_events(candidates)
        detections = [self._event_detection(event, index + 1) for index, event in enumerate(events)]
        elapsed = time.perf_counter() - started
        stats.confirmed_potholes = len(detections)
        stats.inference_seconds = round(elapsed, 4)
        stats.average_fps = round(stats.frames_processed / elapsed, 3) if elapsed else 0.0
        logger.info("Frames Processed count=%s", stats.frames_processed)
        logger.info("Candidate Detections count=%s", stats.candidate_detections)
        logger.info("Confirmed Potholes count=%s", stats.confirmed_potholes)
        logger.info("Inference Time seconds=%.4f", elapsed)
        logger.info("Average FPS value=%.3f", stats.average_fps)
        logger.info("Processing Completed video=%s", video)
        return RoadAnalysisResult(detections=detections, statistics=stats)

    def _pipeline_frames(self, video_path: Path) -> Iterator[SampledFrame]:
        if self._frame_source is None:
            raise RuntimeError(
                "No Processing Pipeline FrameSource is configured for RoadIntelligenceEngine"
            )
        return self._frame_source.iter_sampled_frames(video_path, self._settings.road_fps)

    @staticmethod
    def _valid_frame(image: np.ndarray) -> bool:
        return isinstance(image, np.ndarray) and image.ndim >= 2 and image.size > 0

    def _passes_precision_filters(self, box: BoundingBox, frame: SampledFrame) -> bool:
        if any(_iou(box, vehicle) >= self._settings.vehicle_overlap_threshold for vehicle in frame.vehicle_boxes):
            return False
        if self._settings.roi_enabled:
            height = frame.image.shape[0]
            center_y = (box.y1 + box.y2) / 2
            if center_y < height * self._settings.road_roi_top_ratio:
                return False
        return True

    def _confirmed_events(self, candidates: list[_Candidate]) -> list[_PotholeEvent]:
        """Require repeated adjacent sampled-frame sightings before confirmation."""
        events: list[_PotholeEvent] = []
        for candidate in candidates:
            matching = next(
                (
                    event
                    for event in reversed(events)
                    if event.last_sampled_index == candidate.sampled_index - 1
                    and _same_pothole(event.candidates[-1], candidate, self._settings)
                ),
                None,
            )
            if matching is None:
                matching = _PotholeEvent()
                events.append(matching)
            matching.candidates.append(candidate)
            matching.last_sampled_index = candidate.sampled_index
        return [
            event
            for event in events
            if len({candidate.sampled_index for candidate in event.candidates})
            >= self._settings.min_consecutive_frames
        ]

    def _event_detection(self, event: _PotholeEvent, index: int) -> Detection:
        # Nearby detections are the evidence search window. Confidence is primary,
        # then sharpness, then visible area, matching the evidence policy.
        evidence = max(
            event.candidates,
            key=lambda candidate: (
                candidate.confidence,
                candidate.blur_score,
                candidate.bounding_box.area,
            ),
        )
        return Detection(
            type="POTHOLE",
            timestamp=evidence.timestamp,
            frame_number=evidence.frame_number,
            confidence=evidence.confidence,
            bounding_box=evidence.bounding_box,
            tracking_id=f"pothole-{index:04d}",
            metadata={
                "source": "PeterHdd/pothole-detection-yolo",
                "sampled_frame_count": len(event.candidates),
                "evidence_blur_score": round(evidence.blur_score, 3),
            },
        )


def _iou(first: BoundingBox, second: BoundingBox) -> float:
    """Return intersection-over-union for two xyxy boxes."""
    left, top = max(first.x1, second.x1), max(first.y1, second.y1)
    right, bottom = min(first.x2, second.x2), min(first.y2, second.y2)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    union = first.area + second.area - intersection
    return intersection / union if union else 0.0


def _same_pothole(first: _Candidate, second: _Candidate, settings: Settings) -> bool:
    if _iou(first.bounding_box, second.bounding_box) >= settings.pothole_event_iou:
        return True
    first_center = ((first.bounding_box.x1 + first.bounding_box.x2) / 2, (first.bounding_box.y1 + first.bounding_box.y2) / 2)
    second_center = ((second.bounding_box.x1 + second.bounding_box.x2) / 2, (second.bounding_box.y1 + second.bounding_box.y2) / 2)
    height, width = first.image_shape
    diagonal = max((height**2 + width**2) ** 0.5, 1.0)
    distance = ((first_center[0] - second_center[0]) ** 2 + (first_center[1] - second_center[1]) ** 2) ** 0.5
    return distance / diagonal <= settings.pothole_event_distance


def _sharpness(image: np.ndarray, box: BoundingBox) -> float:
    """Use local Laplacian variance without another video/OpenCV dependency."""
    height, width = image.shape[:2]
    x1, x2 = sorted((max(0, int(box.x1)), min(width, int(box.x2))))
    y1, y2 = sorted((max(0, int(box.y1)), min(height, int(box.y2))))
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return 0.0
    gray = crop.mean(axis=2) if crop.ndim == 3 else crop.astype(float)
    if min(gray.shape) < 3:
        return 0.0
    laplacian = (
        -4 * gray[1:-1, 1:-1]
        + gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
    )
    return float(laplacian.var())
