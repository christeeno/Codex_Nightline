"""Smoke tests for the backend foundation."""

import asyncio
from pathlib import Path

import httpx
from sqlalchemy import inspect

from app.core.config import get_settings
from app.core.database import engine
from app.main import app


def test_system_endpoints_and_openapi() -> None:
    """Expose the required system routes and generated OpenAPI schema."""
    settings = get_settings()

    async def request_system_routes() -> tuple[httpx.Response, ...]:
        transport = httpx.ASGITransport(app=app)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return (
                    await client.get("/"),
                    await client.get("/health"),
                    await client.get("/openapi.json"),
                    await client.get("/docs"),
                )

    root_response, health_response, openapi_response, docs_response = asyncio.run(
        request_system_routes()
    )

    assert root_response.json() == {
        "status": "running",
        "service": "PARA AI Backend",
        "version": "1.0.0",
    }
    assert health_response.json() == {"healthy": True}
    assert openapi_response.status_code == 200
    assert docs_response.status_code == 200
    assert {
        "summary_json",
        "submission_status",
        "video_name",
        "video_duration",
    } <= {column["name"] for column in inspect(engine).get_columns("reports")}
    assert Path(settings.upload_folder).is_dir()
    assert Path(settings.weights_folder).is_dir()
