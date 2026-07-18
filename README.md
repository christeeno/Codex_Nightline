# PARA AI

PARA AI turns citizen-provided dashcam footage into reviewable road-safety reports. It detects motorcycle helmet violations and potholes, attaches timestamped evidence, runs plate OCR only when a helmet violation is confirmed, and can deliver approved reports to a configured government authority after human review.

## Architecture

```text
Dashcam upload → Video reader → Processing orchestrator
                       ├→ Bike-Helmet-Detectionv2 → PaddleOCR (when eligible)
                       └→ PeterHdd pothole YOLO
                                      ↓
                         Incident timeline → Human review
                                      ↓
                  Configured authority API → Citizen dashboard
```

The backend reads the complete video stream. Traffic and road inference are scheduled by timestamp at configurable rates; no duration or frame-count cap is applied. Model objects are cached and reused for subsequent reports.

## Technology stack

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, SQLite, Uvicorn
- Video/evidence: OpenCV
- AI: Ultralytics YOLO, PaddleOCR

## Repository layout

```text
src/                 React citizen and verification interface
backend/app/api/     HTTP workflow endpoints
backend/app/services/ video processing, frame sampling, OCR orchestration
backend/app/adapters/ external-model compatibility boundaries
backend/app/models/  SQLite persistence models
backend/uploads/     runtime videos and evidence (ignored by Git)
backend/weights/     locally supplied model weights (ignored by Git)
docs/                demo and project handoff material
```

## Approved AI dependencies and model setup

| Purpose | Approved source | Weight location |
| --- | --- | --- |
| Helmet violations | `Viddesh1/Bike-Helmet-Detectionv2` | `backend/vendor/Bike-Helmet-Detectionv2/weights/best.pt` (provided vendor checkout), or set `BIKE_HELMET_MODEL_PATH` |
| Potholes | `PeterHdd/pothole-detection-yolo` | Download `best.pt` to `backend/weights/pothole/best.pt` and set `MODEL_PATH` to it |
| License plates | PaddleOCR | PaddleOCR downloads its language models on first local initialization; ensure cache/network access during setup |

The pothole adapter accepts only the pothole class: crack detection is intentionally not part of PARA AI. The helmet adapter requires a no-helmet observation associated with both a rider and motorcycle; pedestrians and cars cannot create helmet violations.

## Installation

Prerequisites: Node.js 20+, Python 3.12+, and model weights described above.

```bash
npm install
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` to point `MODEL_PATH` at the pothole checkpoint if it is not available through the configured URL. Never commit `.env`, weights, uploaded video, or evidence.

### Government delivery setup

Set `GOVERNMENT_SUBMISSION_URL` to the HTTPS endpoint supplied by the relevant authority (or its approved integration gateway). Set `GOVERNMENT_SUBMISSION_API_TOKEN` if that endpoint uses Bearer authentication and name it with `GOVERNMENT_AUTHORITY_NAME` for the receipt shown to the user. Without a URL, the submit action creates a clearly labeled mock report only; it never contacts a real authority.

On submission, PARA AI sends one JSON `POST` containing the report metadata and only the reviewer-approved incidents. Each incident includes its timestamp, confidence, plate/OCR results when available, and (by default) its JPEG evidence as Base64. Set `GOVERNMENT_INCLUDE_EVIDENCE_IMAGES=false` only when the receiving authority has a separate evidence-upload process. A 2xx response is required before the report is marked submitted; a `tracking_id`, `trackingId`, `reference`, `reference_number`, or `id` in that response is displayed as the authority receipt. `POST /mock-government/reports` is available for demo clients to receive a prepared written report and returns a mock reference only.

## Run the application

In one terminal:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

In another terminal:

```bash
npm run dev
```

The API documentation is at `http://localhost:8000/docs`; the Vite application is normally at `http://localhost:3000`.

## API workflow

| Endpoint | Purpose |
| --- | --- |
| `POST /upload` | Upload and validate MP4, MOV, or AVI footage |
| `POST /analyze/{report_id}` | Start background full-video analysis |
| `GET /reports` / `GET /reports/{id}` | List or inspect reports |
| `GET /reports/{id}/progress` | Poll timestamp-accurate progress |
| `GET /reports/{id}/incidents` | Fetch the review timeline |
| `POST /reports/{id}/incidents/{incident_id}/approve` | Approve a reviewed incident |
| `POST /reports/{id}/incidents/{incident_id}/reject` | Reject a false positive |
| `POST /reports/{id}/submit` | Deliver approved incidents to the configured government authority |
| `GET /dashboard` | Fetch current citizen-dashboard totals |

## Demo workflow

1. Upload a prepared dashcam clip.
2. Start analysis and show progress reach 100%.
3. Open the incident timeline and inspect timestamped evidence.
4. Approve or reject each incident with a reviewer.
5. Submit the reviewed report and show the receipt returned by the authority.
6. Open the dashboard to show the updated totals.

## Limitations and future scope

- Plate reading depends on crop size, motion blur, lighting, and camera angle; unreadable plates are returned as `UNKNOWN`.
- Helmet accuracy depends on the supplied model labels and camera angle. The safety-first association rule may miss ambiguous cases rather than report a pedestrian or car.
- Without a configured authority endpoint, government submission produces a mock, send-ready document. It is explicitly not an official filing.
- SQLite is used for hackathon portability, not concurrent production-scale deployment.
- Future work: authenticated user accounts, geolocation, a durable queue, reviewer roles, monitoring, and authority-specific payload adapters.
