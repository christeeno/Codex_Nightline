"""Video processing services and engine orchestration."""

from app.services.license_plate_recognition import LicensePlateRecognitionService

try:
    from app.services.incident_engine import IncidentEngine
except ModuleNotFoundError:  # pragma: no cover - optional in the compact backend build
    IncidentEngine = None  # type: ignore[assignment,misc]

try:
    from app.services.road_intelligence import RoadIntelligenceEngine, SampledFrame
except ModuleNotFoundError:  # pragma: no cover - optional in the compact backend build
    RoadIntelligenceEngine = SampledFrame = None  # type: ignore[assignment,misc]

# The traffic engine is delivered independently; do not prevent the road engine
# from loading while that optional module is absent from a partial checkout.
try:
    from app.services.traffic_violation import TrafficFrame, TrafficViolationEngine
except ModuleNotFoundError:  # pragma: no cover - depends on upstream module delivery
    TrafficFrame = TrafficViolationEngine = None  # type: ignore[assignment,misc]

__all__ = [
    "LicensePlateRecognitionService",
]

if IncidentEngine is not None:
    __all__.append("IncidentEngine")
if RoadIntelligenceEngine is not None:
    __all__.extend(["RoadIntelligenceEngine", "SampledFrame"])

if TrafficViolationEngine is not None:
    __all__.extend(["TrafficFrame", "TrafficViolationEngine"])
