"""Tests for the Bike-Helmet-Detectionv2 traffic integration."""

from types import SimpleNamespace

import numpy as np

from app.adapters.bike_helmet import BikeHelmetAdapter
from app.core.config import Settings
from app.services.traffic_violation import TrafficFrame, TrafficViolationEngine


class FakeBox:
    """A minimal Ultralytics-compatible detection box."""

    def __init__(
        self,
        class_id: int,
        confidence: float,
        coordinates: list[float],
        tracking_id: int | None = None,
    ) -> None:
        self.cls = np.array([class_id])
        self.conf = np.array([confidence])
        self.xyxy = np.array([coordinates])
        self.id = None if tracking_id is None else np.array([tracking_id])


class FakeModel:
    def __init__(self, results: list[list[FakeBox]]) -> None:
        self._results = iter(results)
        self.track_calls = 0

    def to(self, _: str) -> "FakeModel":
        return self

    def track(self, *_: object, **__: object) -> list[SimpleNamespace]:
        self.track_calls += 1
        return [
            SimpleNamespace(
                boxes=next(self._results),
                names={0: "motorcycle", 1: "rider", 2: "no helmet", 3: "person"},
            )
        ]


def _settings(tmp_path, **overrides: object) -> Settings:
    weight = tmp_path / "best.pt"
    weight.write_bytes(b"test-weight")
    return Settings(
        bike_helmet_model_path=str(weight),
        traffic_confidence_threshold=0.40,
        traffic_tracking_iou=0.30,
        **overrides,
    )


def _valid_boxes() -> list[FakeBox]:
    return [
        FakeBox(0, 0.98, [0, 0, 100, 100]),
        FakeBox(1, 0.91, [10, 10, 80, 95]),
        FakeBox(2, 0.83, [25, 12, 45, 35]),
        # These two prove that an arbitrary person/no-helmet pair is ignored.
        FakeBox(3, 0.97, [150, 0, 220, 100]),
        FakeBox(2, 0.94, [170, 12, 190, 35]),
    ]


def test_engine_requires_motorcycle_and_rider_and_reuses_temporary_id(tmp_path) -> None:
    """Only a no-helmet box attached to both entities becomes a violation."""
    settings = _settings(tmp_path)
    model = FakeModel([_valid_boxes(), _valid_boxes()])
    adapter = BikeHelmetAdapter(settings, model_factory=lambda _: model)
    frame = np.zeros((120, 240, 3), dtype=np.uint8)
    result = TrafficViolationEngine(adapter=adapter, settings=settings).analyze_video(
        "complete-video.mp4",
        [TrafficFrame(frame, 0, 0.0), TrafficFrame(frame, 5, 0.5)],
    )

    assert model.track_calls == 2
    assert result.statistics.frames_processed == 2
    assert result.statistics.helmet_violations == 2
    assert result.statistics.triple_riding_violations == 0
    assert len(result.detections) == 2
    assert {item.type for item in result.detections} == {"HELMET_VIOLATION"}
    assert [item.confidence for item in result.detections] == [0.83, 0.83]
    assert result.detections[0].tracking_id == result.detections[1].tracking_id
    assert result.detections[0].metadata["source"] == "Viddesh1/Bike-Helmet-Detectionv2"


def test_upstream_tracking_id_is_preserved(tmp_path) -> None:
    settings = _settings(tmp_path)
    boxes = _valid_boxes()
    boxes[2] = FakeBox(2, 0.83, [25, 12, 45, 35], tracking_id=42)
    adapter = BikeHelmetAdapter(settings, model_factory=lambda _: FakeModel([boxes]))
    frame = np.zeros((120, 240, 3), dtype=np.uint8)

    result = TrafficViolationEngine(adapter=adapter, settings=settings).analyze_video(
        "tracked.mp4", [TrafficFrame(frame, 3, 0.3)]
    )

    assert result.detections[0].tracking_id == "42"


def test_missing_weights_and_invalid_pipeline_are_non_fatal(tmp_path) -> None:
    settings = Settings(bike_helmet_model_path=str(tmp_path / "missing.pt"))
    adapter = BikeHelmetAdapter(settings, model_factory=lambda _: FakeModel([]))
    frame = np.zeros((10, 10, 3), dtype=np.uint8)

    result = TrafficViolationEngine(adapter=adapter, settings=settings).analyze_video(
        "missing-weights.mp4", [TrafficFrame(frame, 0, 0.0)]
    )
    pipeline_error = TrafficViolationEngine(adapter=adapter, settings=settings).analyze_video("broken.mp4")

    assert result.detections == []
    assert result.statistics.frames_processed == 1
    assert pipeline_error.detections == []
    assert pipeline_error.statistics.errors
