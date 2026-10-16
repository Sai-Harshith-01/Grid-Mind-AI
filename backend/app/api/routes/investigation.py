"""FastAPI route handlers for Phase 5 Gemini AI Energy Waste Investigation.

Endpoints:
- GET  /api/investigation/status               : AI readiness status (no secrets exposed)
- POST /api/investigation/anomaly/{anomaly_id} : Grounded investigation of a specific anomaly
- POST /api/investigation/report               : Bounded multi-anomaly diagnostic report
"""

import logging
from fastapi import APIRouter, HTTPException, Path, Query, status
from app.schemas.investigation import (
    InvestigationReportRequest,
    InvestigationReportResponse,
    InvestigationResponse,
    InvestigationStatusResponse,
)
from app.services.factory_data_service import DEFAULT_FACTORY_ID
from app.services.gemini_service import (
    AnomalyNotFoundError,
    GeminiAuthenticationError,
    GeminiMalformedOutputError,
    GeminiRateLimitError,
    GeminiServiceUnavailableError,
    GeminiTimeoutError,
    GeminiUpstreamError,
    gemini_investigation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/investigation", tags=["Gemini AI Energy Waste Investigation"])


@router.get(
    "/status",
    response_model=InvestigationStatusResponse,
    summary="Check Gemini AI service readiness status",
)
def get_investigation_status() -> InvestigationStatusResponse:
    """Return the configuration and readiness status of the Gemini AI engine.
    
    Safe for public consumption: never leaks API keys or secrets.
    """
    return gemini_investigation_service.get_status()


@router.post(
    "/anomaly/{anomaly_id}",
    response_model=InvestigationResponse,
    summary="Investigate a detected factory anomaly with Gemini AI",
    responses={
        200: {"description": "Grounded AI investigation completed successfully."},
        404: {"description": "Specified anomaly ID was not found."},
        429: {"description": "Gemini API rate limit or quota exceeded."},
        502: {"description": "Upstream Gemini service error or malformed response."},
        503: {"description": "Gemini service unavailable (API key not configured)."},
        504: {"description": "Gemini request timed out."},
    },
)
def investigate_anomaly(
    anomaly_id: str = Path(..., description="Unique detected finding ID, e.g. 'FINDING-IDLE-WASTE-H03'"),
    factory_id: str = Query(default=DEFAULT_FACTORY_ID, description="Factory ID to investigate"),
) -> InvestigationResponse:
    """Perform a grounded AI investigation for a specific anomaly.
    
    Retrieves evidence from Phase 3 detector and Phase 4 optimiser, calls Gemini,
    validates structured output, and attaches authoritative backend metrics.
    """
    try:
        return gemini_investigation_service.investigate_anomaly(
            anomaly_id=anomaly_id, factory_id=factory_id
        )
    except AnomalyNotFoundError as exc:
        logger.info("Anomaly not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except GeminiServiceUnavailableError as exc:
        logger.warning("Gemini service unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GeminiAuthenticationError as exc:
        logger.error("Gemini authentication failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini API authentication failed. Verify that GEMINI_API_KEY is valid.",
        ) from exc
    except GeminiRateLimitError as exc:
        logger.warning("Gemini rate limit exceeded: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except GeminiTimeoutError as exc:
        logger.warning("Gemini request timeout: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except GeminiMalformedOutputError as exc:
        logger.error("Gemini malformed output: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini response could not be validated against the required investigation schema.",
        ) from exc
    except GeminiUpstreamError as exc:
        logger.error("Gemini upstream error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini service communication error: {exc}",
        ) from exc



@router.post(
    "/report",
    response_model=InvestigationReportResponse,
    summary="Generate a multi-anomaly diagnostic report with Gemini AI",
    responses={
        200: {"description": "Batch investigation report generated successfully."},
        429: {"description": "Gemini API rate limit or quota exceeded."},
        502: {"description": "Upstream Gemini service error."},
        503: {"description": "Gemini service unavailable (API key not configured)."},
    },
)
def generate_investigation_report(
    request: InvestigationReportRequest = InvestigationReportRequest(),
    factory_id: str = Query(default=DEFAULT_FACTORY_ID, description="Factory ID"),
) -> InvestigationReportResponse:
    """Generate a batch diagnostic report covering prioritised detected anomalies.
    
    Processes anomalies sequentially to prevent rate quota spikes, tracks partial failures,
    and returns a plant-wide synthesis.
    """
    try:
        return gemini_investigation_service.generate_report(
            max_findings=request.max_findings,
            min_severity=request.min_severity,
            factory_id=factory_id,
        )

    except GeminiServiceUnavailableError as exc:
        logger.warning("Gemini service unavailable for report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GeminiAuthenticationError as exc:
        logger.error("Gemini authentication failure in report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini API authentication failed. Verify that GEMINI_API_KEY is valid.",
        ) from exc
    except GeminiRateLimitError as exc:
        logger.warning("Gemini rate limit exceeded in report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except (GeminiUpstreamError, GeminiTimeoutError, GeminiMalformedOutputError) as exc:
        logger.error("Gemini error generating report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate investigation report: {exc}",
        ) from exc
