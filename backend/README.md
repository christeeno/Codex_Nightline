# Para AI Backend

An endpoint-free FastAPI foundation for the Para AI service. It includes application configuration, CORS middleware, structured console logging, and SQLite access through SQLModel. No AI functionality or HTTP endpoints are included in this scaffold.

## Project structure

```text
backend/
├── app/
│   ├── core/       # Settings and logging
│   ├── db/         # SQLModel engine and sessions
│   └── main.py     # FastAPI application setup
├── .env.example    # Runtime configuration template
├── Dockerfile
├── main.py          # ASGI entry point
└── requirements.txt
```

## Run locally

Requires Python 3.12 or newer.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

The service starts its infrastructure lifecycle, initializes the SQLite database at `data/para_ai.db`, and exposes no application routes.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed:

- `APP_NAME`: Name shown in application metadata and logs.
- `ENVIRONMENT`: Deployment environment label.
- `DEBUG`: Enables FastAPI debug mode when `true`.
- `LOG_LEVEL`: Console logging threshold, such as `DEBUG`, `INFO`, or `WARNING`.
- `CORS_ORIGINS`: Comma-separated browser origins allowed by CORS.
- `DATABASE_URL`: SQLAlchemy database URL; defaults to a local SQLite file.

## Run with Docker

From the `backend` directory:

```bash
docker build -t para-ai-backend .
docker run --rm -p 8000:8000 --env-file .env para-ai-backend
```

For durable SQLite data in Docker, mount a host directory at `/app/data`.
