"""Central registration of the public PARA AI workflow."""

from fastapi import APIRouter

from app.api.endpoints.workflow import router as workflow_router


api_router = APIRouter()
api_router.include_router(workflow_router)
