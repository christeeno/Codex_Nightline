# PARA AI Backend

## Project overview

This directory contains the FastAPI foundation for PARA AI. It provides centralized configuration, console logging, SQLite connectivity, CORS, health checks, and a modular route layout.

## Road Intelligence Engine

The Road Intelligence Engine integrates the approved, unmodified [PeterHdd/pothole-detection-yolo](https://github.com/PeterHdd/pothole-detection-yolo) repository as the `backend/vendor/pothole-detection-yolo` submodule, pinned to its upstream commit. `PotholeDetectionAdapter` loads the repository's published pretrained `best.pt` model through Ultralytics and converts its output into PARA AI `Detection` objects.

`RoadIntelligenceEngine` consumes sampled frames from the existing Thread 3 Processing Pipeline through its `FrameSource` contract; it does not open videos or duplicate frame extraction. It uses `ROAD_FPS`, returns only `POTHOLE` detections, and returns `ProcessingStatistics` with every request.

False-positive controls prioritize precision: confidence thresholding, an optional lower-road ROI, supplied vehicle-box overlap rejection, and a minimum number of consecutive sampled-frame sightings. Nearby sightings are grouped into one incident. Evidence uses the confirmed event's highest-confidence frame, then sharpness and visible area as tie-breakers.

Configure the model and filters in `.env` (see `.env.example`). By default `MODEL_PATH` is the weight URL published by the approved repository; set it to a local downloaded `best.pt` path in deployments that cannot download model weights at runtime.

## Folder structure

```text
backend/
├── app/
│   ├── adapters/       # PeterHdd YOLO adapter
│   ├── api/
│   │   ├── endpoints/  # Future route modules
│   │   └── router.py   # Central API router
│   ├── core/           # Configuration, logging, database setup
│   ├── models/         # Future SQLAlchemy models
│   ├── schemas/        # Standardized Detection contracts
│   ├── services/       # Road Intelligence Engine
│   ├── utils/          # Shared utilities
│   └── main.py         # FastAPI application
├── scripts/            # Development scripts
├── tests/              # Backend tests
├── uploads/            # Runtime uploaded files
├── weights/            # Runtime model-weight storage
├── vendor/
│   └── pothole-detection-yolo/ # Approved upstream repository (git submodule)
├── .env.example
├── Dockerfile
├── main.py             # ASGI entry point
└── requirements.txt
```

## Installation

Python 3.12 or newer is required. From this `backend` directory, copy the example environment file and install the dependencies:

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the virtual environment with `.venv\\Scripts\\Activate.ps1`.

## Run commands

Start the development server:

```bash
uvicorn main:app --reload
```

Run the test suite:

```bash
pytest
```

The application creates the configured `uploads/videos`, `uploads/evidence`, and `weights` directories at startup, then initializes the SQLite report table.

## API docs

After starting the server, Swagger UI is available at [http://localhost:8000/docs](http://localhost:8000/docs), and the OpenAPI schema is available at [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json).

System endpoints:

- `GET /` returns service metadata.
- `GET /health` returns the process health status.

## Video processing API

- `POST /reports/upload` accepts a multipart `video` field in MP4, MOV, or AVI format. Files are size-limited by `MAX_UPLOAD_SIZE_MB`, validated by OpenCV, stored under `UPLOAD_PATH`, and processed synchronously for the MVP.
- `GET /reports/{id}/progress` returns in-memory frame counts, timestamp, percentage, ETA, stage, and status.

The pipeline extracts filename, resolution, FPS, frame count, duration, and codec into a report; streams frames sequentially; samples at `TRAFFIC_FPS` and `ROAD_FPS`; and leaves future engine dispatches as typed interfaces only. Source videos are retained. Only disposable `*.tmp` evidence files are removed after processing.

Set `UPLOAD_PATH`, `EVIDENCE_PATH`, `SUPPORTED_FORMATS`, `MAX_UPLOAD_SIZE_MB`, `TRAFFIC_FPS`, and `ROAD_FPS` in `.env` to configure the pipeline.

## Development workflow

Keep configuration in `.env` rather than hardcoding paths or settings. Add route modules under `app/api/endpoints` and register them through `app/api/router.py`. Processing orchestrators should inject their existing sampled-frame provider into `RoadIntelligenceEngine`. Run `pytest` before handing off changes.

## License plates and incidents

Confirmed helmet violations can be enriched through `LicensePlateRecognitionService`. It receives the already-associated motorcycle bounding box, runs the lightweight detector only inside that crop, and sends only a detected plate crop to PaddleOCR. A missing, unreadable, or below-threshold result is returned as `UNKNOWN`; OCR is never run for unrelated detections.

`IncidentEngine` is the boundary that merges traffic and pothole adapter detections. It deduplicates by type, tracking ID, and timestamp proximity, selects one evidence frame by confidence, lower blur, and visible area, then returns standard review-ready incident objects and an aggregate report. The HTTP contract is available at `POST /incidents/generate`.

Tune `OCR_CONFIDENCE`, plate detector sizing/shape thresholds, and incident grouping values through `.env`. PaddleOCR is the only OCR provider used by this service.

## Docker

Build and run the development container from this directory:

```bash
docker build -t para-ai-backend .
docker run --rm -p 8000:8000 --env-file .env para-ai-backend
```
