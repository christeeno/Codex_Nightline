"""Adapter around the PeterHdd pothole model."""
from __future__ import annotations
import logging
from collections.abc import Callable
from typing import Any
import numpy as np
from app.core.config import Settings
from app.schemas import BoundingBox
logger = logging.getLogger(__name__)

class PotholeDetectionAdapter:
    def __init__(self, settings: Settings, model_factory: Callable[[str], Any] | None = None) -> None:
        self._settings, self._model_factory, self._model = settings, model_factory, None
    def load_model(self) -> bool:
        if self._model is not None: return True
        try:
            factory = self._model_factory
            if factory is None:
                from ultralytics import YOLO
                factory = YOLO
            self._model = factory(self._settings.model_path)
            if hasattr(self._model, "to"): self._model.to(self._settings.device)
            return True
        except Exception as exc:
            logger.warning("Pothole model load failed: %s", exc); self._model = None; return False
    def detect(self, frame: np.ndarray) -> list[tuple[BoundingBox, float]]:
        if not self.load_model() or self._model is None: return []
        try:
            results = self._model.predict(frame, conf=self._settings.pothole_confidence, verbose=False)
            if not results: return []
            result, candidates = results[0], []
            for box in getattr(result, "boxes", []) or []:
                class_id = int(_scalar(box.cls)); names = getattr(result, "names", {})
                label = str(names.get(class_id, class_id) if isinstance(names, dict) else names[class_id]).strip().lower()
                confidence = _scalar(box.conf); coords = np.asarray(box.xyxy).reshape(-1).tolist()
                if label in {"pothole", "0"} and confidence >= self._settings.pothole_confidence and len(coords) == 4 and coords[2] > coords[0] and coords[3] > coords[1]: candidates.append((BoundingBox(x1=coords[0], y1=coords[1], x2=coords[2], y2=coords[3]), confidence))
            return candidates
        except Exception as exc:
            logger.warning("Pothole inference failed: %s", exc); return []

def _scalar(value: Any) -> float:
    return float(value.item()) if hasattr(value, "item") else float(np.asarray(value).reshape(-1)[0])
