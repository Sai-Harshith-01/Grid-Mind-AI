"""Root information endpoint router."""

from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import AppInfoResponse

router = APIRouter(tags=["Root"])


@router.get(
    "/",
    response_model=AppInfoResponse,
    summary="Application Overview",
    description="Returns the platform name, description, and interactive docs URL.",
)
async def get_root() -> AppInfoResponse:
    """Return platform metadata and documentation link."""
    return AppInfoResponse(
        name=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
    )
