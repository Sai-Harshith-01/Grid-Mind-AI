"""API routes package."""

from app.api.routes.health import router as health_router
from app.api.routes.root import router as root_router
from app.api.routes.factory import router as factory_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.optimization import router as optimization_router

__all__ = [
    "health_router",
    "root_router",
    "factory_router",
    "analysis_router",
    "optimization_router",
]
