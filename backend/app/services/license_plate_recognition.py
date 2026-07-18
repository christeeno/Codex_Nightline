"""Helmet-violation-scoped license plate recognition orchestration."""

from __future__ import annotations

import logging
import re
from typing import Protocol

import numpy as np

from app.adapters.license_plate_detector import PlateCandidate
from app.adapters.paddle_ocr import OCRText, PaddleOCRAdapter
from app.core.config import Settings, get_settings
from app.schemas.incidents import BoundingBox, LicensePlateResult


logger = logging.getLogger(__name__)
_PLATE_CHARACTERS = re.compile(r"[^A-Z0-9]")


class PlateDetector(Protocol):
    """Boundary implemented by the lightweight plate detector."""

    def detect(self, frame: np.ndarray, motorcycle_bounding_box: BoundingBox) -> PlateCandidate | None: ...


class LicensePlateRecognitionService:
    """Run detection and PaddleOCR only for eligible helmet violations."""

    def __init__(self, detector: PlateDetector, ocr: PaddleOCRAdapter, settings: Settings | None = None):
        self.detector = detector
        self.ocr = ocr
        self.settings = settings or get_settings()

    def recognize(
        self,
        frame: np.ndarray,
        *,
        helmet_violation: bool,
        motorcycle_bounding_box: BoundingBox | None,
    ) -> LicensePlateResult:
        """Recognize one crop, failing closed to ``UNKNOWN`` on every error."""
        if not helmet_violation or motorcycle_bounding_box is None:
            return self._unknown()
        try:
            candidate = self.detector.detect(frame, motorcycle_bounding_box)
            if candidate is None:
                logger.info("No visible plate detected")
                return self._unknown()
            logger.info("Plate detected", extra={"plate_confidence": candidate.confidence})
            if candidate.confidence < self.settings.plate_confidence:
                return self._unknown(candidate.bounding_box, plate_detected=True)
            reading = self.ocr.recognize(candidate.crop)
            if reading is None:
                return self._unknown(candidate.bounding_box, plate_detected=True)
            plate = self._normalise(reading)
            logger.info("OCR confidence", extra={"ocr_confidence": reading.confidence})
            if plate is None or reading.confidence < self.settings.ocr_confidence:
                return self._unknown(candidate.bounding_box, plate_detected=True, confidence=reading.confidence)
            return LicensePlateResult(
                license_plate=plate,
                ocr_confidence=reading.confidence,
                bounding_box=candidate.bounding_box,
                plate_detected=True,
            )
        except Exception:
            logger.exception("License plate recognition failed safely")
            return self._unknown()

    def _unknown(
        self,
        bounding_box: BoundingBox | None = None,
        *,
        plate_detected: bool = False,
        confidence: float = 0.0,
    ) -> LicensePlateResult:
        return LicensePlateResult(
            license_plate=self.settings.unknown_label,
            ocr_confidence=confidence,
            bounding_box=bounding_box,
            plate_detected=plate_detected,
        )

    @staticmethod
    def _normalise(reading: OCRText) -> str | None:
        normalized = _PLATE_CHARACTERS.sub("", reading.text.upper())
        return normalized or None
