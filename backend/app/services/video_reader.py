"""Streaming OpenCV video reader; frames are never buffered as a full video."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class VideoOpenError(ValueError):
    """Raised when OpenCV cannot decode a usable video."""


@dataclass(frozen=True)
class VideoMetadata:
    filename: str
    resolution: str
    fps: float
    frame_count: int
    duration: float
    codec: str


@dataclass(frozen=True)
class VideoFrame:
    image: Any
    frame_number: int
    timestamp: float


class VideoReader:
    """Safely open and sequentially stream frames from one video file."""

    def __init__(self, video_path: str | Path):
        self.video_path = Path(video_path)
        self._capture: Any | None = None
        self._metadata: VideoMetadata | None = None

    def __enter__(self) -> "VideoReader":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def open(self) -> None:
        if not self.video_path.is_file():
            raise VideoOpenError("Uploaded video file is missing.")
        try:
            import cv2
        except Exception as exc:  # pragma: no cover - depends on native libraries
            raise VideoOpenError(
                "OpenCV is unavailable; install opencv-python-headless to process videos."
            ) from exc
        self._capture = cv2.VideoCapture(str(self.video_path))
        if not self._capture.isOpened():
            self.close()
            raise VideoOpenError("Unable to open video. The file may be corrupted.")

        fps = float(self._capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if fps <= 0 or frame_count <= 0 or width <= 0 or height <= 0:
            self.close()
            raise VideoOpenError("Video contains no readable frames or valid timing metadata.")

        ok, _ = self._capture.read()
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if not ok:
            self.close()
            raise VideoOpenError("Video frames cannot be decoded. The file may be corrupted.")

        fourcc = int(self._capture.get(cv2.CAP_PROP_FOURCC))
        codec = "".join(chr((fourcc >> (8 * index)) & 0xFF) for index in range(4)).strip() or "unknown"
        self._metadata = VideoMetadata(
            filename=self.video_path.name,
            resolution=f"{width}x{height}",
            fps=fps,
            frame_count=frame_count,
            duration=frame_count / fps,
            codec=codec,
        )

    @property
    def metadata(self) -> VideoMetadata:
        if self._metadata is None:
            raise RuntimeError("Open the video before reading its metadata.")
        return self._metadata

    def frames(self) -> Iterator[VideoFrame]:
        if self._capture is None or self._metadata is None:
            raise RuntimeError("Open the video before reading frames.")
        frame_number = 0
        while True:
            ok, image = self._capture.read()
            if not ok:
                return
            yield VideoFrame(image=image, frame_number=frame_number, timestamp=frame_number / self._metadata.fps)
            frame_number += 1

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
