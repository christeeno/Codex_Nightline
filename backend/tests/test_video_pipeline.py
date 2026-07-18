"""Regression tests for the synchronous video-processing foundation."""

import asyncio
from pathlib import Path
from tempfile import SpooledTemporaryFile

import cv2
import numpy as np
import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.schemas.detections import Detection, DetectionBatch
from app.services.frame_sampling import FrameSampler
from app.services.orchestrator import ProcessingOrchestrator
from app.services.progress import ProgressRegistry
from app.services.video_reader import VideoOpenError, VideoReader
from app.services.video_storage import UploadValidationError, VideoStorage


def _make_video(path: Path, frames: int = 10, fps: float = 10.0) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), fps, (32, 24))
    assert writer.isOpened()
    for index in range(frames):
        writer.write(np.full((24, 32, 3), index, dtype=np.uint8))
    writer.release()


def test_video_reader_extracts_metadata_and_samples_frames(tmp_path: Path) -> None:
    video = tmp_path / "dashcam.avi"
    _make_video(video)
    with VideoReader(video) as reader:
        metadata = reader.metadata
        sampled = list(FrameSampler(2).sample(reader.frames()))
    assert metadata.filename == "dashcam.avi"
    assert metadata.resolution == "32x24"
    assert metadata.frame_count == 10
    assert metadata.duration == pytest.approx(1.0)
    assert [frame.frame_number for frame in sampled] == [0, 5]


def test_invalid_and_empty_uploads_are_rejected(tmp_path: Path) -> None:
    storage = VideoStorage(tmp_path / "videos", tmp_path / "evidence", 1, frozenset({".avi"}))
    empty_file = SpooledTemporaryFile()
    unsupported_file = SpooledTemporaryFile()
    unsupported_file.write(b"content")
    unsupported_file.seek(0)
    with pytest.raises(UploadValidationError, match="Empty"):
        asyncio.run(storage.save(UploadFile(filename="empty.avi", file=empty_file)))
    with pytest.raises(UploadValidationError, match="Unsupported"):
        asyncio.run(storage.save(UploadFile(filename="video.txt", file=unsupported_file)))


def test_corrupt_video_is_rejected(tmp_path: Path) -> None:
    corrupted = tmp_path / "corrupt.avi"
    corrupted.write_bytes(b"not a video")
    with pytest.raises(VideoOpenError):
        with VideoReader(corrupted):
            pass


def test_orchestrator_tracks_completion_and_preserves_source_video(tmp_path: Path) -> None:
    source = tmp_path / "dashcam.avi"
    _make_video(source)
    storage = VideoStorage(tmp_path / "uploads/videos", tmp_path / "uploads/evidence", 5, frozenset({".avi"}))
    registry = ProgressRegistry()
    orchestrator = ProcessingOrchestrator(storage, traffic_fps=5, road_fps=2, registry=registry)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    report = orchestrator.create_report(session, source, "dashcam.avi")
    result = orchestrator.process(session, report)
    progress = registry.get(report.id)
    assert source.is_file()
    assert result.detections == []
    assert result.frames_processed == 7
    assert progress is not None
    assert progress.percent_complete == 100
    assert progress.status == "completed"


def test_detection_contract_and_temporary_evidence_cleanup(tmp_path: Path) -> None:
    storage = VideoStorage(tmp_path / "videos", tmp_path / "evidence", 1, frozenset({".avi"}))
    temporary = tmp_path / "evidence" / "frame.tmp"
    temporary.write_bytes(b"temporary")
    storage.cleanup_temporary_evidence()
    batch = DetectionBatch(
        detections=[Detection(type="placeholder", timestamp=0, frame_number=0, confidence=0.5)],
        processing_time=0,
        frames_processed=1,
        video_duration=1,
    )
    assert not temporary.exists()
    assert batch.detections[0].type == "placeholder"
