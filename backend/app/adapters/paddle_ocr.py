"""The sole OCR adapter: PaddleOCR, loaded only when a plate crop exists."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from numbers import Real
from typing import Any

import numpy as np

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OCRText:
    """One OCR reading returned by PaddleOCR."""

    text: str
    confidence: float


class PaddleOCRAdapter:
    """Small compatibility boundary around PaddleOCR's result formats."""

    def __init__(self, settings: Settings | None = None, engine: Any | None = None):
        self.settings = settings or get_settings()
        self._engine = engine

    def recognize(self, image: np.ndarray) -> OCRText | None:
        """Read a cropped plate, returning no result instead of raising."""
        if not isinstance(image, np.ndarray) or image.size == 0:
            logger.warning("OCR skipped because the plate crop is invalid")
            return None
        try:
            engine = self._engine or self._load_engine()
            if engine is None:
                return None
            logger.info("OCR started")
            raw_result = engine.ocr(image, cls=self.settings.ocr_use_angle_classification)
            readings = list(self._extract_readings(raw_result))
            if not readings:
                logger.info("OCR completed with no text")
                return None
            result = max(readings, key=lambda reading: reading.confidence)
            logger.info("OCR completed", extra={"ocr_confidence": result.confidence})
            return result
        except Exception:
            logger.exception("PaddleOCR failed safely")
            return None

    def _load_engine(self) -> Any | None:
        try:
            from paddleocr import PaddleOCR

            self._engine = PaddleOCR(lang="en", use_angle_cls=self.settings.ocr_use_angle_classification)
            logger.info("PaddleOCR loaded")
            return self._engine
        except Exception:
            logger.exception("PaddleOCR could not be loaded")
            return None

    @classmethod
    def _extract_readings(cls, value: Any):
        """Yield old and current PaddleOCR `(text, confidence)` result pairs."""
        if isinstance(value, (list, tuple)) and len(value) == 2:
            text, confidence = value
            if isinstance(text, str) and isinstance(confidence, Real):
                yield OCRText(text=text, confidence=max(0.0, min(1.0, float(confidence))))
                return
        if isinstance(value, dict):
            text = value.get("rec_text") or value.get("text")
            confidence = value.get("rec_score") or value.get("confidence")
            if isinstance(text, str) and isinstance(confidence, Real):
                yield OCRText(text=text, confidence=max(0.0, min(1.0, float(confidence))))
            for nested in value.values():
                yield from cls._extract_readings(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                yield from cls._extract_readings(nested)
