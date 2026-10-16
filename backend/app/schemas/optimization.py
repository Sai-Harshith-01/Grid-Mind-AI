"""Pydantic schemas for Phase 4 Renewable Energy Allocation and Optimisation.

All physical units are explicit:
- Energy: kWh
- Power: kW
- Cost / Savings: INR (₹)
- Tariffs: INR per kWh (₹/kWh)
- Timestamps: ISO 8601 strings
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.factory import SimulationMetadata


class IntervalSourceAllocation(BaseModel):
    interval_index: int = Field(..., ge=0, le=23, description="Hour index (0 to 23).")
    timestamp: str = Field(..., description="ISO 8601 timestamp.")
    factory_demand_kwh: float = Field(..., ge=0.0, description="Factory energy demand in kWh.")
    
    # Renewable and grid allocations
    solar_available_kwh: float = Field(..., ge=0.0, description="Simulated available solar energy.")
    solar_allocated_kwh: float = Field(..., ge=0.0, description="Optimised solar allocation in kWh.")
    wind_available_kwh: float = Field(..., ge=0.0, description="Simulated available wind energy.")
    wind_allocated_kwh: float = Field(..., ge=0.0, description="Optimised wind allocation in kWh.")
    biomass_available_kwh: float = Field(..., ge=0.0, description="Dispatchable biomass capacity in kWh.")
    biomass_allocated_kwh: float = Field(..., ge=0.0, description="Optimised biomass allocation in kWh.")
    grid_allocated_kwh: float = Field(..., ge=0.0, description="Optimised grid import in kWh.")
    renewable_allocated_total_kwh: float = Field(..., ge=0.0, description="Sum of renewable allocations (solar+wind+biomass).")
    
    # Financial metrics
    grid_tariff_inr_per_kwh: float = Field(..., ge=0.0, description="Grid tariff for this interval.")
    source_operating_cost_inr: float = Field(..., ge=0.0, description="Renewable source marginal cost (biomass fuel).")
    grid_tariff_cost_inr: float = Field(..., ge=0.0, description="Cost of imported grid electricity.")
    interval_total_cost_inr: float = Field(..., ge=0.0, description="Total supply cost for interval.")
    baseline_grid_cost_inr: float = Field(..., ge=0.0, description="100% grid-only reference cost.")
    interval_savings_inr: float = Field(..., description="Estimated savings for interval (baseline - optimised).")
    
    # Constraints and validation
    unmet_demand_kwh: float = Field(default=0.0, ge=0.0, description="Unserved energy if infeasible.")
    active_constraints: List[str] = Field(default_factory=list, description="Binding constraints for interval.")
    energy_balance_error: float = Field(default=0.0, description="Difference between total supply and demand.")
    is_feasible: bool = Field(default=True, description="Whether interval demand was fully satisfied within limits.")


class SourceUtilizationSummary(BaseModel):
    source: str = Field(..., description="Energy source identifier ('solar', 'wind', 'biomass', 'grid').")
    total_available_kwh: float = Field(..., ge=0.0, description="Total energy available during period.")
    total_allocated_kwh: float = Field(..., ge=0.0, description="Total energy allocated by optimiser.")
    utilization_rate_percent: float = Field(..., ge=0.0, description="Percentage of available energy utilized.")
    total_cost_inr: float = Field(..., ge=0.0, description="Total expenditure on this source.")
    effective_cost_per_kwh_inr: float = Field(..., ge=0.0, description="Average cost per kWh supplied.")


class OptimizationSummaryResponse(BaseModel):
    factory_id: str
    simulation_date: str
    is_feasible: bool = Field(..., description="Whether all intervals were successfully solved without unmet demand.")
    solver_status: str = Field(..., description="Mathematical solver termination status message.")
    
    # Energy totals
    total_demand_kwh: float = Field(..., ge=0.0, description="Total factory demand across intervals.")
    total_demand_served_kwh: float = Field(..., ge=0.0, description="Total energy successfully supplied.")
    unmet_demand_total_kwh: float = Field(default=0.0, ge=0.0, description="Total unserved demand in kWh.")
    
    # Financial performance & savings
    baseline_grid_only_cost_inr: float = Field(..., ge=0.0, description="Reference cost if 100% grid supplied.")
    optimised_supply_cost_inr: float = Field(..., ge=0.0, description="Optimised multi-source supply cost.")
    estimated_savings_inr: float = Field(..., description="Estimated economic savings in INR.")
    estimated_savings_percentage: float = Field(..., description="Percentage reduction against baseline.")
    
    # Mix breakdowns
    renewable_energy_allocated_kwh: float = Field(..., ge=0.0, description="Total renewable energy allocated.")
    renewable_allocation_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Renewable energy share of total served demand (%)."
    )
    grid_energy_allocated_kwh: float = Field(..., ge=0.0, description="Total grid energy allocated.")
    grid_energy_share_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Grid share of total served demand (%)."
    )
    
    # Peak grid parameters
    peak_grid_power_kw: float = Field(..., ge=0.0, description="Peak instantaneous power drawn from grid.")
    peak_grid_contract_utilisation_percent: float = Field(
        ..., ge=0.0, description="Peak grid power relative to contract demand capacity (%)."
    )
    
    # Biomass fuel tracking
    biomass_energy_consumed_kwh: float = Field(..., ge=0.0, description="Biomass electricity dispatched.")
    biomass_fuel_consumed_kg: float = Field(..., ge=0.0, description="Agro-briquette fuel consumed.")
    biomass_remaining_fuel_budget_kg: float = Field(..., ge=0.0, description="Remaining on-site briquette stock.")
    
    infeasible_intervals_count: int = Field(default=0, ge=0, description="Number of infeasible intervals.")
    production_fulfilment_units: Optional[float] = Field(
        None, description="Actual factory finished production supported by served energy."
    )
    baseline_is_capacity_feasible: bool = Field(
        default=True,
        description="Whether 100% grid reference baseline respects the sanctioned contract demand limit.",
    )
    active_scenario_name: str = Field(
        default="Standard Baseline",
        description="Active simulation scenario label (e.g. Standard vs What-If adjustment).",
    )
    solar_multiplier: float = Field(default=1.0, description="Active solar availability multiplier.")
    tariff_multiplier: float = Field(default=1.0, description="Active grid tariff multiplier.")
    disclaimer: str = Field(
        default="Modelled scenario projection based on synthetic telemetry. Not guaranteed commercial savings.",
        description="Simulation disclaimer.",
    )
    simulation_metadata: SimulationMetadata


class OptimizationRunResponse(OptimizationSummaryResponse):
    intervals: List[IntervalSourceAllocation] = Field(
        default_factory=list, description="Hourly allocation schedule across all intervals."
    )
    source_breakdown: List[SourceUtilizationSummary] = Field(
        default_factory=list, description="Per-source availability, allocation, and cost summary."
    )


class HourlyBaselineItem(BaseModel):
    interval_index: int
    timestamp: str
    demand_kwh: float
    demand_kw: float
    grid_tariff_inr_per_kwh: float
    baseline_cost_inr: float
    is_peak_tariff: bool
    exceeds_grid_capacity: bool


class OptimizationBaselineResponse(BaseModel):
    factory_id: str
    simulation_date: str
    total_factory_demand_kwh: float
    grid_contract_demand_kw: float
    is_capacity_feasible: bool
    peak_factory_demand_kw: float
    total_baseline_cost_inr: float
    average_blended_rate_inr_per_kwh: float
    hourly_baseline: List[HourlyBaselineItem]
    simulation_metadata: SimulationMetadata
