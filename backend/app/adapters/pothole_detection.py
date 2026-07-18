"""Adapter around the unchanged PeterHdd pothole-detection-yolo model."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import numpy as np

from app.core.config import Settings
from app.schemas import BoundingBox

logger = logging.getLogger(__name__)


class PotholeDetectionAdapter:
    """Load the approved YOLO model and expose only pothole candidates.

    The upstream repository remains in ``backend/vendor/pothole-detection-yolo``.
    This adapter deliberately owns no upstream code and only translates its YOLO
    result objects into PARA AI primitives.
    """

    def __init__(
        self,
        settings: Settings,
        model_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self._settings = settings
        self._model_factory = model_factory
        self._model: Any | None = None

    def load_model(self) -> bool:
        """Load configured pretrained weights without allowing a backend crash."""
        if self._model is not None:
            return True
        try:
            factory = self._model_factory
            if factory is None:
                from ultralytics import YOLO

                factory = YOLO
            self._model = factory(self._settings.model_path)
            if hasattr(self._model, "to"):
                self._model.to(self._settings.device)
            logger.info(
                "Model Loaded source=PeterHdd/pothole-detection-yolo path=%s device=%s",
                self._settings.model_path,
                self._settings.device,
            )
            return True
        except Exception as exc:  # noqa: BLE001 - inference integrations are fallible
            logger.exception("Pothole model load failed: %s", exc)
            self._model = None
            return False

    def detect(self, frame: np.ndarray) -> list[tuple[BoundingBox, float]]:
        """Return only valid pothole boxes from one already-sampled pipeline frame."""
        if not self.load_model() or self._model is None:
            return []
        try:
            results = self._model.predict(
                frame,
                conf=self._settings.pothole_confidence,
                verbose=False,
            )
            if not results:
                return []
            result = results[0]
            names = getattr(result, "names", {})
            candidates: list[tuple[BoundingBox, float]] = []
            for box in getattr(result, "boxes", []) or []:
                class_id = int(_scalar(box.cls))
                label = str(_class_name(names, class_id)).strip().lower()
                # The upstream service maps class 0 to pothole.  Reject every
                # other label/class so cracks and unrelated hazards never leak.
                if label not in {"pothole", "0"}:
                    continue
                confidence = float(_scalar(box.conf))
                if confidence < self._settings.pothole_confidence:
                    continue
                coordinates = _coordinates(box.xyxy)
                if coordinates is None:
                    continue
                candidates.append(
                    (
                        BoundingBox(
                            x1=coordinates[0],
                            y1=coordinates[1],
                            x2=coordinates[2],
                            y2=coordinates[3],
                        ),
                        confidence,
                    )
                )
            return candidates
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pothole inference failed: %s", exc)
            return []


def _scalar(value: Any) -> float:
    """Convert torch, numpy, or regular scalar values without coupling to torch."""
    if hasattr(value, "item"):
        return float(value.item())
    value = np.asarray(value).reshape(-1)[0]
    return float(value)


def _coordinates(value: Any) -> tuple[float, float, float, float] | None:
    """Extract a single xyxy rectangle from an Ultralytics box object."""
    values = np.asarray(value).reshape(-1).tolist()
    if len(values) != 4:
        return None
    x1, y1, x2, y2 = (float(item) for item in values)
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _class_name(names: Any, class_id: int) -> Any:
    """Read a class name from either YOLO's mapping or list representation."""
    if isinstance(names, dict):
        return names.get(class_id, class_id)
    if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
        return names[class_id]
    return class_id
