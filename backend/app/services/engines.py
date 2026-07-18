"""Extension points for future AI engines. No inference lives here yet."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.schemas.detections import DetectionBatch


class TrafficEngine(ABC):
    @abstractmethod
    def analyze(self, video_path: str | Path) -> DetectionBatch: ...


class PotholeEngine(ABC):
    @abstractmethod
    def analyze(self, video_path: str | Path) -> DetectionBatch: ...


class OCREngine(ABC):
    @abstractmethod
    def recognize(self, image: Any) -> DetectionBatch: ...


class IncidentEngine(ABC):
    @abstractmethod
    def generate(self, detections: list[DetectionBatch]) -> DetectionBatch: ...
