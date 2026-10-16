"""API routes for Phase 3 Energy Analytics and Anomaly Detection — multi-factory."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.data.factory_registry import VALID_FACTORY_IDS, resolve_factory_id
from app.schemas.analysis import (
    AnalyticalEnergyProfileResponse,
    AnomalyListResponse,
    DetectedAnomalyFinding,
    EnergyMetricsSummaryResponse,
)
from app.services.anomaly_detector import anomaly_detector_service
from app.services.energy_metrics import energy_metrics_service
from app.services.factory_data_service import DEFAULT_FACTORY_ID

router = APIRouter(prefix="/api/analysis", tags=["Energy Analytics"])

DEFAULT_FACTORY_DESC = f"Factory ID (default: {DEFAULT_FACTORY_ID}). Valid: {VALID_FACTORY_IDS}"


def _resolve(factory_id: Optional[str]) -> str:
    fid = (factory_id or DEFAULT_FACTORY_ID).strip()
    fid = resolve_factory_id(fid)
    if fid not in VALID_FACTORY_IDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown factory_id '{fid}'. Valid IDs: {VALID_FACTORY_IDS}",
        )
    return fid


@router.get(
    "/metrics",
    response_model=EnergyMetricsSummaryResponse,
    summary="Get Comprehensive Factory Energy Metrics",
    description=(
        "Returns factory-level demand aggregations, zone and shift breakdowns, "
        "renewable energy availability (potential generation), and reference grid-only cost baseline."
    ),
)
async def get_energy_metrics(
    factory_id: Optional[str] = Query(default=None, description=DEFAULT_FACTORY_DESC),
) -> EnergyMetricsSummaryResponse:
    """Return aggregated energy metrics and ToD grid cost baseline."""
    fid = _resolve(factory_id)
    return energy_metrics_service.get_energy_metrics_summary(factory_id=fid)


@router.get(
    "/anomalies",
    response_model=AnomalyListResponse,
    summary="List Detected Industrial Energy Anomalies",
    description=(
        "Returns rule-based detected anomaly findings with optional filters for severity, category, and zone."
    ),
)
async def get_detected_anomalies(
    factory_id: Optional[str] = Query(default=None, description=DEFAULT_FACTORY_DESC),
    severity: Optional[str] = Query(
        None,
        description="Filter by severity level ('low', 'medium', 'high', 'critical')",
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by category ('idle_machine_waste', 'unexpected_consumption_spike', 'high_demand_period')",
    ),
    zone_id: Optional[str] = Query(
        None,
        description="Filter by affected zone ID",
    ),
) -> AnomalyListResponse:
    """Return detected anomaly findings matching optional criteria."""
    fid = _resolve(factory_id)
    return anomaly_detector_service.get_anomalies(
        factory_id=fid, severity=severity, category=category, zone_id=zone_id
    )


@router.get(
    "/anomalies/{anomaly_id}",
    response_model=DetectedAnomalyFinding,
    summary="Get Single Anomaly Finding Details",
    description="Returns detailed evidence, baseline deviation, and physical diagnostic notes for a single anomaly.",
)
async def get_anomaly_detail(
    anomaly_id: str,
    factory_id: Optional[str] = Query(default=None, description=DEFAULT_FACTORY_DESC),
) -> DetectedAnomalyFinding:
    """Return single anomaly finding by identifier or scenario ID. Raises 404 if not found."""
    fid = _resolve(factory_id)
    finding = anomaly_detector_service.get_anomaly_by_id(anomaly_id, factory_id=fid)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Anomaly finding with ID '{anomaly_id}' was not found for factory '{fid}'. "
                "Ensure valid finding ID (e.g. 'FINDING-IDLE-WASTE-H03') or scenario ID."
            ),
        )
    return finding


@router.get(
    "/energy-profile",
    response_model=AnalyticalEnergyProfileResponse,
    summary="Get Hourly Analytical Time Series Profile",
    description=(
        "Returns 24-hour analytical profile including demand in kW and kWh, production throughput, "
        "renewable generation availability by source, grid tariffs, and baseline cost curves."
    ),
)
async def get_analytical_energy_profile(
    factory_id: Optional[str] = Query(default=None, description=DEFAULT_FACTORY_DESC),
) -> AnalyticalEnergyProfileResponse:
    """Return 24-hour analytical profile with hourly costs and renewable yields."""
    fid = _resolve(factory_id)
    return energy_metrics_service.get_energy_profile(factory_id=fid)
