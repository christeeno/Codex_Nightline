"""Video processing services and engine orchestration."""

from app.services.incident_engine import IncidentEngine
from app.services.license_plate_recognition import LicensePlateRecognitionService
from app.services.road_intelligence import RoadIntelligenceEngine, SampledFrame

# The traffic engine is delivered independently; do not prevent the road engine
# from loading while that optional module is absent from a partial checkout.
try:
    from app.services.traffic_violation import TrafficFrame, TrafficViolationEngine
except ModuleNotFoundError:  # pragma: no cover - depends on upstream module delivery
    TrafficFrame = TrafficViolationEngine = None  # type: ignore[assignment,misc]

__all__ = [
    "IncidentEngine",
    "LicensePlateRecognitionService",
    "RoadIntelligenceEngine",
    "SampledFrame",
]

if TrafficViolationEngine is not None:
    __all__.extend(["TrafficFrame", "TrafficViolationEngine"])
