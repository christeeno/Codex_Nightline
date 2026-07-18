"""Safe on-disk handling for uploaded videos and disposable evidence files."""

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


logger = logging.getLogger(__name__)


class UploadValidationError(ValueError):
    """Raised when a client upload does not meet video storage requirements."""


class VideoStorage:
    def __init__(self, upload_path: str | Path, evidence_path: str | Path, max_size_mb: int, extensions: frozenset[str]):
        self.upload_path = Path(upload_path)
        self.evidence_path = Path(evidence_path)
        self.max_bytes = max_size_mb * 1024 * 1024
        self.extensions = extensions
        self.upload_path.mkdir(parents=True, exist_ok=True)
        self.evidence_path.mkdir(parents=True, exist_ok=True)

    async def save(self, upload: UploadFile) -> Path:
        filename = Path(upload.filename or "").name
        extension = Path(filename).suffix.lower()
        if not filename:
            raise UploadValidationError("A video filename is required.")
        if extension not in self.extensions:
            allowed = ", ".join(sorted(self.extensions))
            raise UploadValidationError(f"Unsupported video format. Accepted formats: {allowed}.")

        temporary = self.upload_path / f".{uuid4()}.uploading"
        destination = self.upload_path / f"{uuid4()}{extension}"
        written = 0
        logger.info("Upload started", extra={"event": "upload_started", "source_filename": filename})
        try:
            with temporary.open("wb") as target:
                while chunk := await upload.read(1024 * 1024):
                    written += len(chunk)
                    if written > self.max_bytes:
                        raise UploadValidationError("Video exceeds the configured maximum upload size.")
                    target.write(chunk)
            if written == 0:
                raise UploadValidationError("Empty video files cannot be processed.")
            temporary.replace(destination)
            logger.info("Upload completed", extra={"event": "upload_completed", "source_filename": filename, "bytes": written})
            return destination
        except Exception:
            temporary.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            logger.exception("Upload failed", extra={"event": "upload_failed", "source_filename": filename})
            raise
        finally:
            await upload.close()

    def cleanup_temporary_evidence(self) -> None:
        """Remove only files explicitly marked temporary; never source videos."""
        for path in self.evidence_path.glob("*.tmp"):
            path.unlink(missing_ok=True)
