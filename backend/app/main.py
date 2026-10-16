"""GridMind AI FastAPI Application Entrypoint.

Provides the foundational REST API services, CORS middleware,
health check endpoints, Phase 2 Synthetic Factory Data Engine,
Phase 3 Energy Analysis & Anomaly Detection, Phase 4 Renewable
Energy Allocation & Optimisation, and Phase 5 Gemini AI Investigation.

Multi-factory support: all data endpoints accept a factory_id query parameter.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.root import router as root_router
from app.api.routes.factory import router as factory_router, router_legacy as factory_legacy_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.optimization import router as optimization_router
from app.api.routes.investigation import router as investigation_router


def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register Routers
    application.include_router(root_router)
    application.include_router(health_router)
    application.include_router(factory_router)         # /api/factories
    application.include_router(factory_legacy_router)  # /api/factory/* (backward compat)
    application.include_router(analysis_router)
    application.include_router(optimization_router)
    application.include_router(investigation_router)

    return application


app = create_application()

