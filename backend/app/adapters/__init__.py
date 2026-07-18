"""External model adapters."""

from app.adapters.license_plate_detector import OpenCVPlateDetector, PlateCandidate
from app.adapters.paddle_ocr import OCRText, PaddleOCRAdapter
from app.adapters.pothole_detection import PotholeDetectionAdapter

# The approved helmet adapter is delivered independently.  Keep unrelated
# adapters importable until that optional integration is present.
try:
    from app.adapters.bike_helmet import BikeHelmetAdapter
except ModuleNotFoundError:  # pragma: no cover - depends on upstream module delivery
    BikeHelmetAdapter = None  # type: ignore[assignment,misc]

__all__ = [
    "OCRText",
    "OpenCVPlateDetector",
    "PaddleOCRAdapter",
    "PlateCandidate",
    "PotholeDetectionAdapter",
]

if BikeHelmetAdapter is not None:
    __all__.append("BikeHelmetAdapter")
