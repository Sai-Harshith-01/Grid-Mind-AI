"""API routes for Phase 4 Renewable Energy Allocation and Optimisation — multi-factory."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.data.factory_registry import VALID_FACTORY_IDS, resolve_factory_id
from app.schemas.optimization import (
    OptimizationBaselineResponse,
    OptimizationRunResponse,
    OptimizationSummaryResponse,
)
from app.services.energy_optimizer import EnergyOptimizerService
from app.services.factory_data_service import DEFAULT_FACTORY_ID

router = APIRouter(prefix="/api/optimization", tags=["Energy Optimisation"])

DEFAULT_FACTORY_DESC = f"Factory ID (default: {DEFAULT_FACTORY_ID}). Valid: {VALID_FACTORY_IDS}"

_optimizer = EnergyOptimizerService()


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
    "/baseline",
    response_model=OptimizationBaselineResponse,
    summary="Get 100% Grid-Only Reference Baseline",
    description=(
        "Returns the reference scenario where 100% of factory demand is procured from the utility grid "
        "under multi-tier Time-of-Day (ToD) tariffs, checking contract demand capacity feasibility."
    ),
)
async def get_optimization_baseline(
    factory_id: Optional[str] = Query(default=None, description=DEFAULT_FACTORY_DESC),
    tariff_multiplier: float = Query(
        default=1.0, ge=0.1, le=5.0, description="Tariff adjustment multiplier (1.0 = standard)"
    ),
) -> OptimizationBaselineResponse:
    """Return grid-only reference cost baseline and hourly demand profile."""
    fid = _resolve(factory_id)
    return _optimizer.get_baseline(factory_id=fid, tariff_multiplier=tariff_multiplier)


@router.get(
    "/run",
    response_model=OptimizationRunResponse,
    summary="Execute Renewable Energy Dispatch Optimisation",
    description=(
        "Runs deterministic linear programming (HiGHS solver) to minimize total electricity costs, "
        "allocating solar, wind, and biomass generation alongside grid electricity to satisfy factory demand."
    ),
)
async def run_optimization(
    factory_id: Optional[str] = Query(default=None, description=DEFAULT_FACTORY_DESC),
    solar_multiplier: float = Query(
        default=1.0, ge=0.0, le=5.0, description="Solar availability multiplier (1.0 = standard)"
    ),
    tariff_multiplier: float = Query(
        default=1.0, ge=0.1, le=5.0, description="Tariff adjustment multiplier (1.0 = standard)"
    ),
) -> OptimizationRunResponse:
    """Execute full linear programming optimization and return hourly source allocations."""
    fid = _resolve(factory_id)
    return _optimizer.run_optimization(
        factory_id=fid,
        solar_multiplier=solar_multiplier,
        tariff_multiplier=tariff_multiplier,
    )


@router.get(
    "/summary",
    response_model=OptimizationSummaryResponse,
    summary="Get Optimisation Performance Summary",
    description=(
        "Returns an executive dashboard summary of optimisation results: estimated economic savings, "
        "renewable allocation percentage, peak grid power, and biomass fuel consumption."
    ),
)
async def get_optimization_summary(
    factory_id: Optional[str] = Query(default=None, description=DEFAULT_FACTORY_DESC),
    solar_multiplier: float = Query(
        default=1.0, ge=0.0, le=5.0, description="Solar availability multiplier (1.0 = standard)"
    ),
    tariff_multiplier: float = Query(
        default=1.0, ge=0.1, le=5.0, description="Tariff adjustment multiplier (1.0 = standard)"
    ),
) -> OptimizationSummaryResponse:
    """Return high-level economic and operational performance summary."""
    fid = _resolve(factory_id)
    return _optimizer.get_summary(
        factory_id=fid,
        solar_multiplier=solar_multiplier,
        tariff_multiplier=tariff_multiplier,
    )
