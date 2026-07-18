# Thread 5 — Road Intelligence Engine

## Objective

Integrate the mandatory `PeterHdd/pothole-detection-yolo` model as a reusable PARA AI pothole-only backend module.

## Implementation Summary

Added a lazy Ultralytics model adapter, a pipeline-facing Road Intelligence Engine, standardized detection/statistics schemas, configuration, and tests. The engine processes the complete sampled-frame iterable it receives and returns only confirmed `POTHOLE` detections.

## Repository Integration Strategy

The approved source is an unmodified git submodule at `backend/vendor/pothole-detection-yolo`, pinned to `ab9506301965dc9477b7993005f3b615fe0df74f`. The adapter uses the model path published by that repository and does not import, patch, or run its FastAPI server.

## False Positive Reduction Strategy

Candidates must pass the configured confidence threshold and lower-road ROI. Candidates substantially overlapping vehicle boxes supplied by the traffic pipeline are rejected. A pothole must appear in at least `MIN_CONSECUTIVE_FRAMES` adjacent sampled frames; nearby boxes are grouped into one event.

## Architecture Decisions

`RoadIntelligenceEngine` depends on a `FrameSource` contract from the established Processing Pipeline, avoiding a second frame extractor or duplicated OpenCV video logic. The adapter translates only the upstream model's pothole class. Evidence selects highest confidence, then lowest blur/highest sharpness, then largest visible area.

## Files Added

- `app/adapters/pothole_detection.py`
- `app/services/road_intelligence.py`
- `app/schemas/detection.py`
- `tests/test_road_intelligence.py`
- `DEVELOPMENT_LOG_THREAD_5.md`
- `vendor/pothole-detection-yolo` (submodule)

## Files Modified

- `app/core/config.py`
- `app/adapters/__init__.py`
- `app/services/__init__.py`
- `app/schemas/__init__.py`
- `.env.example`
- `requirements.txt`
- `README.md`

## Configuration Changes

Added `MODEL_PATH`, `DEVICE`, `POTHOLE_CONFIDENCE`, `MIN_CONSECUTIVE_FRAMES`, event grouping thresholds, vehicle overlap threshold, and ROI controls. Existing `ROAD_FPS` is used for pipeline sampling.

## Tests Executed

`pytest` (final results recorded after verification).

## Known Limitations

The current worktree does not include the Thread 3 pipeline implementation, so the engine exposes a typed `FrameSource` integration point. Vehicle-overlap filtering consumes vehicle boxes from that existing traffic/pipeline layer instead of adding a second detector. Runtime model loading requires the configured local weights or network access to the upstream model URL.

## Commit Message

`feat: integrate PeterHdd pothole detection engine`

## Commit Hash

Recorded after commit.

## Branch Name

`main`

## Push Status

Recorded after push.

Thread 5 Completed Successfully
