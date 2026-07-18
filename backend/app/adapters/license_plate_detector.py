"""A small OpenCV plate detector constrained to an associated motorcycle."""

from __future__ import annotations

from dataclasses import dataclass
import logging

import cv2
import numpy as np

from app.core.config import Settings, get_settings
from app.schemas.incidents import BoundingBox


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlateCandidate:
    """A detected plate crop and its coordinates in the original frame."""

    bounding_box: BoundingBox
    crop: np.ndarray
    confidence: float


class OpenCVPlateDetector:
    """Find rectangular plate-like regions only inside a motorcycle box.

    This deliberately does not inspect the whole image.  It is a lightweight
    detector suitable for a first local pass and can be replaced through the
    same ``detect`` boundary without changing either traffic engine.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def detect(
        self, frame: np.ndarray, motorcycle_bounding_box: BoundingBox
    ) -> PlateCandidate | None:
        """Return the highest-scoring plate candidate inside one motorcycle."""
        try:
            if not isinstance(frame, np.ndarray) or frame.ndim < 2:
                logger.warning("Plate detection skipped because the frame is invalid")
                return None
            bounds = self._clamp(motorcycle_bounding_box, frame.shape[:2])
            if bounds is None:
                logger.warning("Plate detection skipped because motorcycle crop is invalid")
                return None

            x1, y1, x2, y2 = (int(bounds.left), int(bounds.top), int(bounds.right), int(bounds.bottom))
            motorcycle_crop = frame[y1:y2, x1:x2]
            if motorcycle_crop.size == 0:
                return None
            gray = cv2.cvtColor(motorcycle_crop, cv2.COLOR_BGR2GRAY)
            kernel = self.settings.plate_blur_kernel_size
            if kernel % 2 == 0:
                kernel += 1
            blurred = cv2.GaussianBlur(gray, (kernel, kernel), 0)
            edges = cv2.Canny(
                blurred,
                self.settings.plate_canny_lower_threshold,
                self.settings.plate_canny_upper_threshold,
            )
            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            candidates: list[PlateCandidate] = []
            for contour in contours:
                local_x, local_y, width, height = cv2.boundingRect(contour)
                if not self._is_plausible(width, height):
                    continue
                contour_area = cv2.contourArea(contour)
                rectangle_fill = contour_area / max(width * height, 1)
                score = min(1.0, max(0.0, (rectangle_fill + 0.5) / 1.5))
                box = BoundingBox(
                    left=x1 + local_x,
                    top=y1 + local_y,
                    right=x1 + local_x + width,
                    bottom=y1 + local_y + height,
                )
                candidates.append(
                    PlateCandidate(
                        bounding_box=box,
                        crop=frame[int(box.top):int(box.bottom), int(box.left):int(box.right)].copy(),
                        confidence=score,
                    )
                )
            if not candidates:
                return None
            candidate = max(candidates, key=lambda item: item.confidence)
            logger.info("Plate detected", extra={"confidence": candidate.confidence})
            return candidate
        except Exception:
            logger.exception("Plate detection failed safely")
            return None

    def _is_plausible(self, width: int, height: int) -> bool:
        if min(width, height) < self.settings.min_plate_size:
            return False
        if max(width, height) > self.settings.max_plate_size or height <= 0:
            return False
        aspect_ratio = width / height
        return self.settings.min_plate_aspect_ratio <= aspect_ratio <= self.settings.max_plate_aspect_ratio

    @staticmethod
    def _clamp(box: BoundingBox, shape: tuple[int, int]) -> BoundingBox | None:
        height, width = shape
        left, right = sorted((max(0.0, box.left), min(float(width), box.right)))
        top, bottom = sorted((max(0.0, box.top), min(float(height), box.bottom)))
        if right <= left or bottom <= top:
            return None
        return BoundingBox(left=left, top=top, right=right, bottom=bottom)
