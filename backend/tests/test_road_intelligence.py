"""Unit/integration-style tests for the PeterHdd pothole adapter."""

from types import SimpleNamespace

import numpy as np

from app.adapters import PotholeDetectionAdapter
from app.core.config import Settings
from app.schemas import BoundingBox
from app.services import RoadIntelligenceEngine, SampledFrame


class FakeBox:
    """Minimal Ultralytics-compatible box used without model weights."""

    def __init__(self, class_id: int, confidence: float, coordinates: list[float]) -> None:
        self.cls = np.array([class_id])
        self.conf = np.array([confidence])
        self.xyxy = np.array([coordinates])


class FakeModel:
    def __init__(self, results: list[list[FakeBox]]) -> None:
        self._results = iter(results)

    def to(self, _: str) -> "FakeModel":
        return self

    def predict(self, *_: object, **__: object) -> list[SimpleNamespace]:
        return [SimpleNamespace(boxes=next(self._results), names={0: "pothole", 1: "longitudinal crack"})]


def _settings(**overrides: object) -> Settings:
    return Settings(
        pothole_confidence=0.55,
        min_consecutive_frames=2,
        roi_enabled=True,
        road_roi_top_ratio=0.35,
        **overrides,
    )


def test_engine_returns_only_confirmed_potholes_and_statistics() -> None:
    """Cracks, one-frame sightings, and vehicle overlaps are discarded."""
    model = FakeModel(
        [
            [FakeBox(0, 0.75, [20, 70, 50, 100]), FakeBox(1, 0.99, [5, 70, 20, 90])],
            [FakeBox(0, 0.80, [22, 70, 52, 100])],
            [FakeBox(0, 0.95, [80, 70, 110, 100])],
            [FakeBox(0, 0.99, [60, 70, 90, 100])],
        ]
    )
    settings = _settings()
    adapter = PotholeDetectionAdapter(settings, model_factory=lambda _: model)
    frame = np.indices((120, 120)).sum(axis=0).astype(np.uint8)
    frames = [
        SampledFrame(frame, 0, 0.0),
        SampledFrame(frame, 15, 0.5),
        SampledFrame(frame, 30, 1.0),
        SampledFrame(frame, 45, 1.5, vehicle_boxes=(BoundingBox(x1=60, y1=70, x2=90, y2=100),)),
    ]

    result = RoadIntelligenceEngine(adapter=adapter, settings=settings).analyze_video(
        "fixture.mp4", frames
    )

    assert result.statistics.frames_processed == 4
    assert result.statistics.candidate_detections == 3
    assert result.statistics.confirmed_potholes == 1
    assert len(result.detections) == 1
    detection = result.detections[0]
    assert detection.type == "POTHOLE"
    assert detection.frame_number == 15
    assert detection.confidence == 0.80
    assert detection.metadata["sampled_frame_count"] == 2


def test_model_failure_and_missing_pipeline_do_not_crash() -> None:
    """Missing weights and a missing pipeline become empty, reported responses."""
    settings = _settings()
    adapter = PotholeDetectionAdapter(
        settings, model_factory=lambda _: (_ for _ in ()).throw(FileNotFoundError("weights missing"))
    )
    assert adapter.load_model() is False

    result = RoadIntelligenceEngine(adapter=adapter, settings=settings).analyze_video("missing.mp4")

    assert result.detections == []
    assert result.statistics.frames_processed == 0
    assert result.statistics.errors
