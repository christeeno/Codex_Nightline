"""Focused tests for the Thread 6 OCR pipeline and incident engine."""

import numpy as np

from app.adapters.license_plate_detector import PlateCandidate
from app.adapters.paddle_ocr import PaddleOCRAdapter
from app.schemas.incidents import BoundingBox, DetectionInput
from app.services.incident_engine import IncidentEngine
from app.services.license_plate_recognition import LicensePlateRecognitionService


class _Detector:
    def __init__(self, candidate: PlateCandidate | None):
        self.candidate = candidate
        self.calls = 0

    def detect(self, frame: np.ndarray, motorcycle_bounding_box: BoundingBox) -> PlateCandidate | None:
        self.calls += 1
        return self.candidate


class _PaddleEngine:
    def __init__(self, text: str = "MH 12 AB 1234", confidence: float = 0.92):
        self.text = text
        self.confidence = confidence
        self.calls = 0

    def ocr(self, image: np.ndarray, cls: bool):
        self.calls += 1
        return [[[[0, 0], [1, 0], [1, 1], [0, 1]], (self.text, self.confidence)]]


def _box() -> BoundingBox:
    return BoundingBox(left=1, top=1, right=20, bottom=8)


def test_ocr_reads_only_a_detected_plate_crop() -> None:
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    detector = _Detector(PlateCandidate(_box(), image[1:8, 1:20], 0.9))
    paddle = _PaddleEngine()
    service = LicensePlateRecognitionService(detector, PaddleOCRAdapter(engine=paddle))

    result = service.recognize(image, helmet_violation=True, motorcycle_bounding_box=_box())

    assert result.license_plate == "MH12AB1234"
    assert result.ocr_confidence == 0.92
    assert result.plate_detected is True
    assert detector.calls == 1
    assert paddle.calls == 1


def test_low_confidence_and_ineligible_ocr_return_unknown() -> None:
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    detector = _Detector(PlateCandidate(_box(), image[1:8, 1:20], 0.9))
    paddle = _PaddleEngine(confidence=0.2)
    service = LicensePlateRecognitionService(detector, PaddleOCRAdapter(engine=paddle))

    low_confidence = service.recognize(image, helmet_violation=True, motorcycle_bounding_box=_box())
    ineligible = service.recognize(image, helmet_violation=False, motorcycle_bounding_box=None)

    assert low_confidence.license_plate == "UNKNOWN"
    assert low_confidence.ocr_confidence == 0.2
    assert ineligible.license_plate == "UNKNOWN"
    assert detector.calls == 1
    assert paddle.calls == 1


def test_incidents_deduplicate_select_evidence_and_generate_report() -> None:
    engine = IncidentEngine()
    traffic = [
        DetectionInput(
            type="helmet violation",
            timestamp=2.0,
            confidence=0.9,
            tracking_id="bike-7",
            evidence_image="soft.jpg",
            frame_index=10,
            blur_score=12,
            object_area=200,
        ),
        DetectionInput(
            type="helmet_violation",
            timestamp=3.0,
            confidence=0.9,
            tracking_id="bike-7",
            evidence_image="sharp.jpg",
            frame_index=11,
            blur_score=2,
            object_area=120,
            license_plate="MH12AB1234",
            ocr_confidence=0.93,
        ),
        DetectionInput(
            type="triple_riding",
            timestamp=8.0,
            confidence=0.8,
            tracking_id="bike-9",
            evidence_image="triple.jpg",
        ),
    ]
    potholes = [
        DetectionInput(type="pothole", timestamp=4.0, confidence=0.7, tracking_id="p-1", evidence_image="pothole.jpg")
    ]

    incidents = engine.generate(traffic, potholes)
    report = engine.generate_report(incidents, video_duration_seconds=15.0, processing_time_seconds=2.5)

    assert [item.type for item in incidents] == ["helmet_violation", "pothole", "triple_riding"]
    helmet = incidents[0]
    assert helmet.evidence_image == "sharp.jpg"
    assert helmet.license_plate == "MH12AB1234"
    assert helmet.metadata["detection_count"] == 2
    assert report.model_dump() == {
        "video_duration_seconds": 15.0,
        "processing_time_seconds": 2.5,
        "helmet_violations": 1,
        "triple_riding": 1,
        "potholes": 1,
        "reports_ready": 3,
    }
