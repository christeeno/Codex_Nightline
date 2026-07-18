# Thread 6 Development Log — License Plate Recognition & Incident Engine

## Objective

Enrich eligible helmet violations with license-plate data using PaddleOCR and
turn normalized traffic/pothole detections into review-ready incidents.

## Implementation Summary

- Added a motorcycle-box-constrained OpenCV plate detector.
- Added the PaddleOCR-only adapter with lazy loading and safe failure handling.
- Added a recognition service that invokes OCR only for a helmet violation with
  an associated motorcycle and a detected plate crop.
- Added normalized incident and report schemas, a deduplicating
  `IncidentEngine`, and `POST /incidents/generate`.

## OCR Integration Strategy

PaddleOCR is the only OCR provider. It is imported only when a valid plate crop
exists. Missing dependency/model, invalid crop, no text, and confidence below
`OCR_CONFIDENCE` return `UNKNOWN` rather than inferred text.

## Incident Engine Design

Adapter outputs are merged, ordered by timestamp, and grouped by detection type,
tracking ID, and `INCIDENT_DEDUPLICATION_SECONDS`. One standard incident is
created per resulting event.

## Evidence Selection Strategy

Event-neighbouring detections are ranked by highest confidence, lowest blur, and
largest visible object area. Only the selected frame path is emitted as evidence.

## Architecture Decisions

Traffic and pothole engines are not modified. The OCR pipeline and incident
engine consume their normalized adapter outputs through independent contracts.

## Files Added

- `app/adapters/license_plate_detector.py`
- `app/adapters/paddle_ocr.py`
- `app/services/license_plate_recognition.py`
- `app/services/incident_engine.py`
- `app/schemas/incidents.py`
- `app/api/endpoints/incidents.py`
- `tests/test_license_plate_and_incidents.py`

## Files Modified

- `app/core/config.py`
- `app/api/router.py`
- `app/adapters/__init__.py`
- `app/services/__init__.py`
- `app/schemas/__init__.py`
- `requirements.txt`
- `.env.example`
- `README.md`

## Configuration Changes

Added OCR confidence, plate confidence/size/aspect/Canny values, unknown-label,
and incident de-duplication/evidence settings. PaddleOCR and PaddlePaddle are
declared in `requirements.txt`.

## Tests Executed

- `backend/.venv/bin/python -m pytest backend/tests -q` — 11 passed.
- `backend/.venv/bin/python -m compileall -q backend/app` — passed.
- `git diff --check` — passed.

## Known Limitations

The local virtual environment could not install PaddleOCR because its pip
metadata resolver raised `TypeError: expected string or bytes-like object, got
'NoneType'`. A clean environment installing `backend/requirements.txt` provides
the required runtime dependency; the service fails closed to `UNKNOWN` until it
is available.

## Git Status

- Requested commit message: `feat: implement OCR pipeline and incident engine`
- Current branch: `main`
- Existing commit containing the Thread 6 implementation: `0784d4f`
- Push status: not performed in this run because concurrent workspace changes
  left unrelated tracked files deleted/modified; committing or pushing them
  would risk overwriting another milestone's work.

Thread 6 Completed Successfully
