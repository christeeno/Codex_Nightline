"""FastAPI application and infrastructure initialization."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.api.router import api_router
from app.core.database import initialize_database
from app.core.logging import configure_logging


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize local infrastructure needed by the application."""
    Path(settings.upload_folder).mkdir(parents=True, exist_ok=True)
    Path(settings.upload_path).mkdir(parents=True, exist_ok=True)
    Path(settings.evidence_path).mkdir(parents=True, exist_ok=True)
    Path(settings.weights_folder).mkdir(parents=True, exist_ok=True)
    initialize_database()
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Stopping %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    description="Upload dashcam footage, run AI analysis, review incidents, and submit a mock report.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return invalid request details using the common response envelope."""
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "Request validation failed", "errors": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Return expected API errors using the common response envelope."""
    errors = exc.detail if isinstance(exc.detail, list) else [exc.detail]
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": "Request failed", "errors": errors},
    )


@app.get("/", tags=["system"])
async def read_root() -> dict[str, str]:
    """Return service metadata for a lightweight availability check."""
    return {
        "status": "running",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/health", tags=["system"])
async def read_health() -> dict[str, bool]:
    """Return the health status of the backend process."""
    return {"healthy": True}
