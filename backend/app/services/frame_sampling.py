"""Configurable timestamp-based frame sampling."""

from collections.abc import Iterator

from app.services.video_reader import VideoFrame


class FrameSampler:
    """Yield frames at a target rate without assuming a fixed source FPS."""

    def __init__(self, target_fps: float):
        if target_fps <= 0:
            raise ValueError("Sampling FPS must be greater than zero.")
        self.target_fps = target_fps

    def sample(self, frames: Iterator[VideoFrame]) -> Iterator[VideoFrame]:
        next_timestamp = 0.0
        interval = 1 / self.target_fps
        for frame in frames:
            if frame.timestamp + 1e-9 < next_timestamp:
                continue
            yield frame
            while next_timestamp <= frame.timestamp + 1e-9:
                next_timestamp += interval

    def accepts(self, frame: VideoFrame, next_timestamp: float) -> tuple[bool, float]:
        """Return whether a frame is due and the next schedule timestamp."""
        if frame.timestamp + 1e-9 < next_timestamp:
            return False, next_timestamp
        interval = 1 / self.target_fps
        while next_timestamp <= frame.timestamp + 1e-9:
            next_timestamp += interval
        return True, next_timestamp
