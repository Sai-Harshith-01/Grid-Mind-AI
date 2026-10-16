"""API router for factory data endpoints — multi-factory support.

All endpoints accept an optional factory_id query parameter.
Default factory is DEMO-FAC-001 (PrecisionWorks Factory).
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.data.factory_registry import VALID_FACTORY_IDS, resolve_factory_id
from app.schemas.factory import (
    AnomalyScenariosResponse,
    FactoryListItem,
    FactoryListResponse,
    FactoryOverviewResponse,
    FactoryProfileResponse,
    FactoryTimeSeriesResponse,
)
from app.services.factory_data_service import factory_data_service, DEFAULT_FACTORY_ID

router = APIRouter(tags=["Factory Engine"])

FACTORY_DEMO_SCENARIOS = {
    "DEMO-FAC-001": (
        "Off-shift electricity waste and unusual machine loads. "
        "Detect off-shift electricity waste in CNC machining, investigate with Gemini, "
        "run HiGHS optimisation, and compare grid-only vs. multi-source costs."
    ),
    "DEMO-FAC-002": (
        "Peak demand and refrigeration electricity consumption. "
        "Identify high-demand cold-storage intervals during expensive peak tariffs, "
        "optimise source allocation, and explain the modelled cost difference."
    ),
    "DEMO-FAC-003": (
        "Shift-based electricity demand and renewable-energy optimisation. "
        "Optimise renewable dispatch across spinning and weaving shifts, and explain "
        "grid dependence relative to solar and wind availability."
    ),
}


def _resolve_factory_id(factory_id: Optional[str]) -> str:
    fid = (factory_id or DEFAULT_FACTORY_ID).strip()
    fid = resolve_factory_id(fid)
    if fid not in VALID_FACTORY_IDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown factory_id '{fid}'. Valid IDs: {VALID_FACTORY_IDS}",
        )
    return fid


@router.get(
    "/api/factories",
    response_model=FactoryListResponse,
    summary="List All Configured Demo Factories",
    description="Returns compact summaries of all three configured demo factory profiles.",
    tags=["Factory Engine"],
)
async def list_factories() -> FactoryListResponse:
    """Return the list of all configured demo factory IDs, names, and summaries."""
    items = []
    for fid in VALID_FACTORY_IDS:
        profile = factory_data_service.get_raw_profile(fid)
        items.append(
            FactoryListItem(
                factory_id=profile.factory_id,
                name=profile.name,
                sector=profile.sector,
                location=profile.location,
                total_rated_connected_power_kw=profile.total_rated_connected_power_kw,
                grid_contract_demand_kw=profile.grid.contract_demand_kw,
                solar_capacity_kw=profile.solar.installed_capacity_kw,
                wind_capacity_kw=profile.wind.installed_capacity_kw,
                biomass_capacity_kw=profile.biomass.installed_capacity_kw,
                demo_scenario_description=FACTORY_DEMO_SCENARIOS.get(fid, ""),
            )
        )
    return FactoryListResponse(total_factories=len(items), factories=items)


@router.get(
    "/api/factories/{factory_id}",
    response_model=FactoryProfileResponse,
    summary="Get Factory Profile by ID",
    description="Returns the full factory configuration for the specified factory ID.",
    tags=["Factory Engine"],
)
async def get_factory_by_id(factory_id: str) -> FactoryProfileResponse:
    """Return full factory asset profile for a specific factory ID."""
    fid = _resolve_factory_id(factory_id)
    return factory_data_service.get_profile(fid)


# Legacy /api/factory/ endpoints preserved for backward compatibility
# They now honour the factory_id query parameter.

router_legacy = APIRouter(prefix="/api/factory", tags=["Factory Engine"])


@router_legacy.get(
    "/profile",
    response_model=FactoryProfileResponse,
    summary="Get Factory Profile and Architecture",
    description="Returns the factory configuration for the selected factory. Pass factory_id query param to switch factories.",
)
async def get_factory_profile(
    factory_id: Optional[str] = Query(default=None, description="Factory ID, e.g. DEMO-FAC-001"),
) -> FactoryProfileResponse:
    """Return factory asset profile and simulation metadata."""
    fid = _resolve_factory_id(factory_id)
    return factory_data_service.get_profile(fid)


@router_legacy.get(
    "/timeseries",
    response_model=FactoryTimeSeriesResponse,
    summary="Get 24-Hour Factory Time Series",
    description="Returns the complete 24-hour deterministic simulated readings for the selected factory.",
)
async def get_factory_timeseries(
    factory_id: Optional[str] = Query(default=None, description="Factory ID"),
) -> FactoryTimeSeriesResponse:
    """Return the ordered 24-hour simulated readings."""
    fid = _resolve_factory_id(factory_id)
    return factory_data_service.get_timeseries(fid)


@router_legacy.get(
    "/anomaly-scenarios",
    response_model=AnomalyScenariosResponse,
    summary="Get Injected Anomaly Scenarios",
    description="Returns the predefined, reproducible anomaly events and diagnostic metadata.",
)
async def get_anomaly_scenarios(
    factory_id: Optional[str] = Query(default=None, description="Factory ID"),
) -> AnomalyScenariosResponse:
    """Return the predefined reproducible anomaly scenarios."""
    fid = _resolve_factory_id(factory_id)
    return factory_data_service.get_anomaly_scenarios(fid)


@router_legacy.get(
    "/overview",
    response_model=FactoryOverviewResponse,
    summary="Get Factory Dataset Summary Overview",
    description="Returns high-level descriptive metrics derived from the 24-hour dataset.",
)
async def get_factory_overview(
    factory_id: Optional[str] = Query(default=None, description="Factory ID"),
) -> FactoryOverviewResponse:
    """Return basic metrics, peak demand, and renewable availability summary."""
    fid = _resolve_factory_id(factory_id)
    return factory_data_service.get_overview(fid)
