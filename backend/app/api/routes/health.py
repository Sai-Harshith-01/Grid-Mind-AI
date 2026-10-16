"""Health check endpoint router."""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Status",
    description="Returns the operational health, version, and server timestamp.",
)
async def get_health() -> HealthResponse:
    """Return current service health and UTC timestamp."""
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
    )
