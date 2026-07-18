# PARA AI

## Project Overview

PARA AI turns dashcam footage into actionable road intelligence. It helps teams identify traffic violations and road-surface hazards, review detected incidents, and prepare information for civic reporting.

## Features

- Upload MP4, MOV, or AVI dashcam footage for analysis.
- Detect traffic violations, missing helmets, triple riding, and potholes.
- Review confidence, evidence, location, and status for each incident.
- Track processing progress and dashboard metrics.
- Store uploaded footage and generated evidence through the FastAPI backend.

## Architecture Diagram

```text
Dashcam footage
      |
      v
React + Vite frontend  --->  FastAPI API  --->  Processing pipeline
      |                         |                    |
      v                         v                    v
Dashboard and review UI      SQLite storage      Detection models
                                                     |
                                                     v
                                           Incident records and evidence
```

## Technology Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, Lucide icons
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, SQLite
- Computer vision: Ultralytics YOLO, OpenCV, PaddleOCR
- Tooling: npm and pytest

## AI Models Used

- YOLO-based pothole detection, provided by the vendored `pothole-detection-yolo` project.
- Helmet and vehicle detection adapters for traffic-safety analysis.
- PaddleOCR for license-plate text extraction.
- Gemini integration is configured through `GEMINI_API_KEY` when enabled by the application.

## Installation

Prerequisites: Node.js 20+ and Python 3.12+.

```bash
git clone https://github.com/christeeno/Codex_Nightline.git
cd Codex_Nightline
npm install
```

Set optional frontend configuration in `.env.local`:

```bash
GEMINI_API_KEY=your_api_key
VITE_API_URL=http://localhost:8000
```

Install the backend dependencies:

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the virtual environment with `.venv\\Scripts\\Activate.ps1`.

## Running Frontend

From the repository root:

```bash
npm run dev
```

Open the URL reported by Vite (normally `http://localhost:3000`).

## Running Backend

From the `backend` directory with the virtual environment active:

```bash
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`, with interactive documentation at `http://localhost:8000/docs`.

## Demo Workflow

1. Start the backend and frontend services.
2. Open PARA AI and select **Upload Footage**.
3. Upload a supported dashcam video.
4. Allow the processing pipeline to sample frames and create detections.
5. Review incidents in the console, including confidence and evidence.
6. Approve or reject incidents and use the dashboard to monitor results.

## Folder Structure

```text
.
├── src/                    # React frontend
│   ├── components/          # Views and interface components
│   ├── App.tsx              # Application state and routing
│   └── main.tsx             # Frontend entry point
├── backend/
│   ├── app/                 # FastAPI routes, services, models, and adapters
│   ├── tests/               # Backend test suite
│   ├── uploads/             # Runtime video and evidence storage
│   └── vendor/              # Pinned computer-vision dependencies
├── package.json
└── README.md
```

## Future Work

- Connect the frontend upload flow to the live processing API.
- Add asynchronous job execution and live progress updates.
- Improve incident geolocation and map-based triage.
- Add role-based access control and audit trails.
- Expand model evaluation, monitoring, and human-review workflows.
