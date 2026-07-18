"""Centralized runtime configuration for the PARA AI backend."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables with local defaults."""

    app_name: str = "PARA AI Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = "sqlite:///./para.db"
    upload_folder: str = "uploads"
    upload_path: str = "uploads/videos"
    evidence_path: str = "uploads/evidence"
    weights_folder: str = "weights"
    traffic_fps: int = 5
    road_fps: int = 2
    traffic_confidence_threshold: float = 0.40
    traffic_tracking_iou: float = 0.30
    bike_helmet_model_path: str = "vendor/Bike-Helmet-Detectionv2/weights/best.pt"
    bike_helmet_device: str = "cpu"
    bike_helmet_tracker: str = "bytetrack.yaml"
    bike_helmet_motorcycle_labels: str = "motorcycle,bike,motorbike"
    bike_helmet_rider_labels: str = "rider,bike rider,motorcycle rider"
    bike_helmet_no_helmet_labels: str = "no helmet,no_helmet,nohelmet,without helmet,without_helmet"
    pothole_confidence: float = 0.55
    min_consecutive_frames: int = 2
    pothole_event_iou: float = 0.15
    pothole_event_distance: float = 0.20
    vehicle_overlap_threshold: float = 0.40
    roi_enabled: bool = True
    road_roi_top_ratio: float = 0.35
    device: str = "cpu"
    model_path: str = (
        "https://huggingface.co/peterhdd/pothole-detection-yolov8/resolve/main/best.pt"
    )
    helmet_model_path: str = "vendor/Bike-Helmet-Detectionv2/weights/best.pt"
    # Dashcam footage is commonly larger than 100 MB; deployments can lower
    # this through MAX_UPLOAD_SIZE_MB when storage limits require it.
    max_upload_size_mb: int = 500
    supported_formats: str = "mp4,mov,avi"
    log_level: str = "INFO"
    # Vite uses 5173 by default, while this project runs its development UI on
    # 3000. Allow both common local origins (and their loopback equivalents).
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    # Government reporting is opt-in.  A deployment must point this at the
    # receiving authority's REST endpoint; without it no report can be sent.
    government_submission_url: str | None = None
    government_submission_api_token: str | None = None
    government_authority_name: str = "government authority"
    government_submission_timeout_seconds: float = 20.0
    government_include_evidence_images: bool = True

    # License-plate recognition values are deployment-specific and must not
    # be embedded in the detector or OCR pipeline.
    ocr_confidence: float = 0.80
    plate_confidence: float = 0.40
    min_plate_size: int = 20
    max_plate_size: int = 800
    min_plate_aspect_ratio: float = 1.5
    max_plate_aspect_ratio: float = 7.0
    plate_blur_kernel_size: int = 5
    plate_canny_lower_threshold: int = 75
    plate_canny_upper_threshold: int = 200
    unknown_label: str = "UNKNOWN"
    ocr_use_angle_classification: bool = True

    # Incident grouping and evidence selection.
    incident_deduplication_seconds: float = 3.0
    incident_neighbour_frame_window: int = 5
    incident_default_status: str = "pending_review"
    # Allows local/demo analysis to complete with warnings when a vision-model
    # dependency or weight is unavailable. Set false to require model-only results.
    demo_inference: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Return normalized CORS origins from the comma-separated setting."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Video extensions accepted by the upload endpoint."""
        return frozenset(
            f".{item.strip().lstrip('.').lower()}"
            for item in self.supported_formats.split(",")
            if item.strip()
        )

    @staticmethod
    def _label_set(value: str) -> frozenset[str]:
        """Normalize a comma-separated detector class allow-list."""
        return frozenset(
            item.strip().lower().replace("_", " ")
            for item in value.split(",")
            if item.strip()
        )

    @property
    def motorcycle_labels(self) -> frozenset[str]:
        return self._label_set(self.bike_helmet_motorcycle_labels)

    @property
    def rider_labels(self) -> frozenset[str]:
        return self._label_set(self.bike_helmet_rider_labels)

    @property
    def no_helmet_labels(self) -> frozenset[str]:
        return self._label_set(self.bike_helmet_no_helmet_labels)

@lru_cache
def get_settings() -> Settings:
    """Create and cache the process settings instance."""
    return Settings()
