"""Pydantic schemas for Phase 3 Energy Analysis, Metrics, and Anomaly Detection.

All physical units are explicit:
- Power: kW
- Energy: kWh
- Cost: INR (₹)
- Production: units / parts
- Timestamps: ISO 8601 strings with timezone
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.factory import SimulationMetadata


class DemandMetrics(BaseModel):
    total_demand_kwh: float = Field(..., description="Total cumulative factory energy demand in kWh.")
    average_hourly_demand_kwh: float = Field(..., description="Average energy consumed per 1-hour interval in kWh.")
    average_power_kw: float = Field(..., description="Mean instantaneous power across observation period in kW.")
    peak_power_kw: float = Field(..., description="Highest recorded power demand in kW.")
    peak_power_interval_index: int = Field(..., description="Hour index of highest demand (0 to 23).")
    peak_power_timestamp: str = Field(..., description="ISO 8601 timestamp of peak demand interval.")
    total_production_units: float = Field(..., description="Total units of production completed.")
    overall_energy_intensity_kwh_per_unit: Optional[float] = Field(
        None, description="Energy intensity in kWh/unit. None if zero production."
    )


class ZoneMetric(BaseModel):
    zone_id: str
    zone_name: str
    total_consumption_kwh: float = Field(..., description="Total energy consumed by zone in kWh.")
    average_power_kw: float = Field(..., description="Average active power in kW.")
    peak_power_kw: float = Field(..., description="Peak power reached by zone in kW.")
    percentage_of_total_demand: float = Field(..., description="Zone share of total factory energy demand (%).")
    total_production_units: float = Field(..., description="Total units produced by zone.")
    energy_intensity_kwh_per_unit: Optional[float] = Field(
        None, description="Zone-specific energy intensity (kWh/unit). None if zero production."
    )


class ShiftMetric(BaseModel):
    shift_name: str
    hours_count: int
    total_consumption_kwh: float
    average_demand_kw: float
    percentage_of_total_demand: float
    total_production_units: float


class RenewableSourceAvailability(BaseModel):
    source: str = Field(..., description="Renewable energy stream ('solar', 'wind', 'biomass').")
    total_available_kwh: float = Field(..., ge=0.0, description="Cumulative available energy in kWh.")
    average_available_kw: float = Field(..., ge=0.0, description="Average available generation rate in kW.")
    peak_available_kw: float = Field(..., ge=0.0, description="Peak available generation rate in kW.")
    installed_capacity_kw: float = Field(..., gt=0.0, description="Nameplate installed capacity in kW.")
    capacity_factor_percent: float = Field(..., ge=0.0, le=100.0, description="Observed capacity factor (%).")


class RenewableAvailabilityMetrics(BaseModel):
    sources: List[RenewableSourceAvailability]
    total_renewable_available_kwh: float = Field(..., ge=0.0, description="Combined renewable available energy.")
    availability_to_demand_ratio_percent: float = Field(
        ..., ge=0.0, description="Total available renewable energy relative to total factory demand (%)."
    )
    disclaimer: str = Field(
        default=(
            "Available renewable energy represents maximum potential generation under simulated weather/fuel conditions. "
            "It does NOT represent actual energy supplied, allocated, or consumed by the factory."
        )
    )


class TariffPeriodCost(BaseModel):
    period_name: str
    tariff_rate_inr_per_kwh: float
    hours_count: int
    energy_demand_kwh: float
    estimated_cost_inr: float
    percentage_of_total_cost: float


class GridCostBaseline(BaseModel):
    total_estimated_cost_inr: float = Field(
        ..., ge=0.0, description="Estimated grid-only electricity cost assuming 100% grid procurement."
    )
    average_blended_rate_inr_per_kwh: float = Field(
        ..., ge=0.0, description="Effective blended electricity tariff in INR/kWh."
    )
    period_breakdown: List[TariffPeriodCost]
    grid_contract_demand_kw: float = Field(..., description="Contract demand sanctioned limit in kW.")
    max_demand_kw: float = Field(..., description="Observed peak demand in kW.")
    exceeds_grid_capacity: bool = Field(..., description="True if any interval exceeded contract demand.")
    capacity_headroom_kw: float = Field(
        ..., description="Difference between contract demand and peak demand (positive = safe, negative = breach)."
    )
    description: str = Field(
        default=(
            "Reference baseline calculating the factory electricity bill if all energy demand were supplied "
            "exclusively by the utility grid under Time-of-Day tariffs, before any renewable self-consumption."
        )
    )


class ProductionAnalysis(BaseModel):
    total_production_units: float
    idle_or_unproductive_intervals: List[int] = Field(
        default_factory=list, description="Hours with zero scheduled production but positive energy consumption."
    )
    idle_consumption_total_kwh: float = Field(
        default=0.0, description="Total energy consumed during zero-production intervals."
    )


class EnergyMetricsSummaryResponse(BaseModel):
    factory_id: str
    factory_name: str
    simulation_date: str
    demand_metrics: DemandMetrics
    zone_metrics: List[ZoneMetric]
    shift_metrics: List[ShiftMetric]
    renewable_availability: RenewableAvailabilityMetrics
    grid_cost_baseline: GridCostBaseline
    production_analysis: ProductionAnalysis
    simulation_metadata: SimulationMetadata


class AnomalyEvidence(BaseModel):
    interval_index: int
    timestamp: str
    metric_name: str
    observed_value: float
    baseline_threshold: float
    deviation_value: float
    deviation_percent: float
    unit: str
    grid_tariff_inr_per_kwh: Optional[float] = None


class DetectedAnomalyFinding(BaseModel):
    finding_id: str = Field(..., description="Unique detected finding identifier.")
    scenario_id: Optional[str] = Field(None, description="Associated injected scenario ID if applicable.")
    category: str = Field(..., description="Category: idle_machine_waste, unexpected_consumption_spike, high_demand_period.")
    title: str = Field(..., description="Concise human-readable finding title.")
    severity: str = Field(..., description="Severity classification: low, medium, high, critical.")
    affected_zone_id: Optional[str] = None
    affected_zone_name: Optional[str] = None
    affected_machine_id: Optional[str] = None
    affected_machine_name: Optional[str] = None
    interval_index: int
    timestamp: str
    evidence: AnomalyEvidence
    detection_rule_id: str
    detection_rule_description: str
    physical_hypothesis_notes: str
    estimated_financial_impact_inr: Optional[float] = Field(
        None, description="Estimated monetary impact (excess energy x interval tariff) in INR."
    )
    suggested_action: str
    is_synthetic: bool = True


class AnomalyListResponse(BaseModel):
    total_detected: int
    findings: List[DetectedAnomalyFinding]
    severity_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    simulation_metadata: SimulationMetadata


class HourlyAnalyticalProfileItem(BaseModel):
    interval_index: int
    timestamp: str
    factory_demand_kw: float
    factory_demand_kwh: float
    production_units: float
    energy_intensity_kwh_per_unit: Optional[float] = None
    solar_available_kwh: float
    wind_available_kwh: float
    biomass_available_kwh: float
    total_renewable_available_kwh: float
    grid_tariff_inr_per_kwh: float
    grid_cost_baseline_inr: float
    active_anomalies: List[str]
    is_peak_tariff: bool
    shift_name: str
    is_production_active: bool


class AnalyticalEnergyProfileResponse(BaseModel):
    factory_id: str
    factory_name: str
    simulation_date: str
    total_intervals: int
    hourly_profile: List[HourlyAnalyticalProfileItem]
    summary_totals: Dict[str, float]
    simulation_metadata: SimulationMetadata
