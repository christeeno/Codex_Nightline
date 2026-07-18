# PARA AI Project Summary

## Problem statement

Road-safety reports are difficult to document consistently from citizen footage. Manual review of long clips delays reporting and provides little structured evidence.

## Solution

PARA AI converts dashcam footage into a human-reviewable timeline of high-confidence helmet-violation and pothole incidents. Each item preserves its video timestamp, confidence, evidence frame, and—only for eligible helmet events—an OCR plate reading.

## Architecture and workflow

The system follows a deliberately narrow flow: upload → full-video reader → traffic and road engines → OCR for confirmed motorcycle helmet events → incident timeline → reviewer decision → mock submission → dashboard.

SQLite records reports, incidents, evidence, and mock submissions. FastAPI provides the documented API and React provides the citizen-facing experience.

## AI stack

- Bike-Helmet-Detectionv2 for motorcycle helmet signals
- PeterHdd/pothole-detection-yolo for potholes only
- PaddleOCR for license-plate crops after confirmed helmet violations

## Key decisions

- The helmet path fails closed: a no-helmet label must be associated with rider and motorcycle labels. This prevents pedestrian and car false positives.
- Crack classes are excluded at the road adapter boundary.
- Model instances are retained between reports to avoid repeated expensive initialization.
- Human verification precedes every submission.

## Demo flow

Upload a dashcam clip, start analysis, poll its progress, review the generated incidents, approve/reject them, submit the report, and open the dashboard to show the result.

## Known limitations

Model confidence depends on source footage, labels, lighting, occlusion, and camera angle. Plate OCR may return `UNKNOWN`. The submission is a local mock; SQLite and in-process background processing are hackathon choices, not a production-scale deployment model.

## Future scope

Add real agency integration, durable jobs, authentication and reviewer roles, geolocation, model evaluation datasets, notification workflows, and production observability.
