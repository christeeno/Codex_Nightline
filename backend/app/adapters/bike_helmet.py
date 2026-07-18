"""Compatibility adapter for the unchanged Bike-Helmet-Detectionv2 repository."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import Settings, get_settings
from app.schemas.detection import BoundingBox


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HelmetViolationCandidate:
    """A no-helmet observation proven to belong to a bike-rider detection."""

    bounding_box: BoundingBox
    confidence: float
    rider_box: BoundingBox
    motorcycle_box: BoundingBox
    tracking_id: str | None
    source_label: str


@dataclass(frozen=True)
class _UpstreamBox:
    label: str
    bounding_box: BoundingBox
    confidence: float
    tracking_id: str | None


class BikeHelmetAdapter:
    """Translate the approved YOLOv8 model output into traffic candidates.

    The adapter intentionally does not import the upstream Streamlit UI or
    duplicate its frame extraction. It invokes its supplied ``best.pt`` via
    Ultralytics, matching the repository's ``helper.load_model`` mechanism.
    """

    source_name = "Viddesh1/Bike-Helmet-Detectionv2"

    def __init__(
        self,
        settings: Settings | None = None,
        model_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._model_factory = model_factory
        self._model: Any | None = None
        self._load_attempted = False

    @property
    def model_path(self) -> Path:
        return Path(self._settings.bike_helmet_model_path)

    def load_model(self) -> bool:
        """Load upstream pretrained weights once, returning failure safely."""
        if self._model is not None:
            return True
        if self._load_attempted:
            return False
        self._load_attempted = True
        try:
            if not self.model_path.is_file():
                raise FileNotFoundError(f"Bike-Helmet-Detectionv2 weights are missing: {self.model_path}")
            factory = self._model_factory
            if factory is None:
                from ultralytics import YOLO

                factory = YOLO
            self._model = factory(str(self.model_path))
            if hasattr(self._model, "to"):
                self._model.to(self._settings.bike_helmet_device)
            logger.info(
                "Model loaded source=%s path=%s device=%s",
                self.source_name,
                self.model_path,
                self._settings.bike_helmet_device,
            )
            return True
        except Exception as exc:  # noqa: BLE001 - model providers are external
            self._model = None
            logger.exception("Bike helmet model loading failed: %s", exc)
            return False

    def detect(self, frame: np.ndarray) -> list[HelmetViolationCandidate]:
        """Return no-helmet boxes associated with the model's bike-rider class.

        Bike-Helmet-Detectionv2 exposes ``Bike_Rider``, ``Helmet``, and
        ``No_Helmet`` classes.  It does *not* expose a separate motorcycle
        class, so requiring one here silently filters every legitimate result.
        A ``Bike_Rider`` box already represents the rider-and-bike pair and is
        also the safest available crop for downstream plate recognition.
        """
        if not isinstance(frame, np.ndarray) or frame.ndim < 2 or frame.size == 0:
            logger.warning("Bike helmet inference skipped because the frame is invalid")
            return []
        if not self.load_model() or self._model is None:
            return []
        try:
            # The approved repository exposes tracking through ``model.track``.
            results = self._model.track(
                frame,
                conf=self._settings.traffic_confidence_threshold,
                persist=True,
                tracker=self._settings.bike_helmet_tracker,
                verbose=False,
            )
            if not results:
                return []
            boxes = self._extract_boxes(results[0])
            motorcycles = [box for box in boxes if box.label in self._settings.motorcycle_labels]
            riders = [box for box in boxes if box.label in self._settings.rider_labels]
            no_helmets = [box for box in boxes if box.label in self._settings.no_helmet_labels]

            candidates: list[HelmetViolationCandidate] = []
            for no_helmet in no_helmets:
                rider = _best_overlap(no_helmet.bounding_box, riders)
                if rider is None:
                    continue
                # Some compatible custom weights may include a motorcycle
                # class. Prefer it when present; the upstream model does not,
                # so the Bike_Rider detection is the meaningful fallback.
                motorcycle = _best_overlap(rider.bounding_box, motorcycles) or rider
                candidates.append(
                    HelmetViolationCandidate(
                        bounding_box=no_helmet.bounding_box,
                        confidence=no_helmet.confidence,
                        rider_box=rider.bounding_box,
                        motorcycle_box=motorcycle.bounding_box,
                        tracking_id=no_helmet.tracking_id or rider.tracking_id,
                        source_label=no_helmet.label,
                    )
                )
            return candidates
        except Exception as exc:  # noqa: BLE001
            logger.exception("Bike helmet inference failed: %s", exc)
            return []

    def _extract_boxes(self, result: Any) -> list[_UpstreamBox]:
        names = getattr(result, "names", {})
        output: list[_UpstreamBox] = []
        for box in getattr(result, "boxes", []) or []:
            coordinates = _coordinates(getattr(box, "xyxy", None))
            if coordinates is None:
                continue
            confidence = _scalar(getattr(box, "conf", None))
            if confidence < self._settings.traffic_confidence_threshold:
                continue
            class_id = int(_scalar(getattr(box, "cls", None)))
            label = _normalized_label(_class_name(names, class_id))
            output.append(
                _UpstreamBox(
                    label=label,
                    bounding_box=BoundingBox(x1=coordinates[0], y1=coordinates[1], x2=coordinates[2], y2=coordinates[3]),
                    confidence=confidence,
                    tracking_id=_tracking_id(getattr(box, "id", None)),
                )
            )
        return output


def _scalar(value: Any) -> float:
    if value is None:
        raise ValueError("upstream box has no scalar value")
    if hasattr(value, "item"):
        return float(value.item())
    return float(np.asarray(value).reshape(-1)[0])


def _tracking_id(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return str(int(_scalar(value)))
    except (TypeError, ValueError, IndexError):
        return None


def _coordinates(value: Any) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    values = np.asarray(value).reshape(-1).tolist()
    if len(values) != 4:
        return None
    x1, y1, x2, y2 = (float(item) for item in values)
    return (x1, y1, x2, y2) if x2 > x1 and y2 > y1 else None


def _class_name(names: Any, class_id: int) -> Any:
    if isinstance(names, dict):
        return names.get(class_id, class_id)
    if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
        return names[class_id]
    return class_id


def _normalized_label(value: Any) -> str:
    return str(value).strip().lower().replace("_", " ")


def _best_overlap(target: BoundingBox, choices: list[_UpstreamBox]) -> _UpstreamBox | None:
    """Return the intersecting box with the greatest overlap ratio."""
    matches = [choice for choice in choices if _overlap_ratio(target, choice.bounding_box) > 0]
    return max(matches, key=lambda choice: _overlap_ratio(target, choice.bounding_box), default=None)


def _overlap_ratio(first: BoundingBox, second: BoundingBox) -> float:
    left, top = max(first.x1, second.x1), max(first.y1, second.y1)
    right, bottom = min(first.x2, second.x2), min(first.y2, second.y2)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    return intersection / max(min(first.area, second.area), 1.0)
