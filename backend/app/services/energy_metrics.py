"""Energy metrics and analytics service for GridMind AI.

Performs robust, deterministic calculations for:
- Factory demand aggregations (kWh, average kW, peak kW, intensity)
- Zone and machine consumption breakdowns
- Shift-based consumption and throughput
- Renewable energy availability by source (potential generation)
- Grid-only electricity cost baselines under Time-of-Day (ToD) tariffs
- Production analysis and idle consumption identification
"""

from typing import Dict, List, Optional
from app.data.factory_config import FactoryProfile, GridConfig, ProductionZoneConfig, ShiftSchedule
from app.schemas.analysis import (
    AnalyticalEnergyProfileResponse,
    DemandMetrics,
    EnergyMetricsSummaryResponse,
    GridCostBaseline,
    HourlyAnalyticalProfileItem,
    ProductionAnalysis,
    RenewableAvailabilityMetrics,
    RenewableSourceAvailability,
    ShiftMetric,
    TariffPeriodCost,
    ZoneMetric,
)
from app.schemas.factory import SimulationMetadata, TimeSeriesInterval
from app.services.factory_data_service import factory_data_service, DEFAULT_FACTORY_ID


class EnergyMetricsService:
    """Service providing pure, testable energy analytics functions."""

    @staticmethod
    def calculate_demand_metrics(intervals: List[TimeSeriesInterval]) -> DemandMetrics:
        """Calculate factory-level aggregate demand metrics across intervals."""
        if not intervals:
            raise ValueError("Cannot calculate demand metrics on empty intervals list.")

        total_demand_kwh = round(sum(i.total_factory_energy_demand_kwh for i in intervals), 2)
        total_intervals = len(intervals)
        avg_hourly_demand_kwh = round(total_demand_kwh / total_intervals, 2)

        # Average power in kW = total energy / total hours (since intervals are hourly)
        total_hours = sum(i.interval_duration_hours for i in intervals)
        avg_power_kw = round(total_demand_kwh / total_hours, 2) if total_hours > 0 else 0.0

        # Peak power interval
        peak_interval = max(intervals, key=lambda i: i.total_factory_demand_kw)
        peak_power_kw = round(peak_interval.total_factory_demand_kw, 2)

        # Production metrics
        total_production = round(sum(i.actual_production_output_units for i in intervals), 1)
        energy_intensity = (
            round(total_demand_kwh / total_production, 4) if total_production > 0 else None
        )

        return DemandMetrics(
            total_demand_kwh=total_demand_kwh,
            average_hourly_demand_kwh=avg_hourly_demand_kwh,
            average_power_kw=avg_power_kw,
            peak_power_kw=peak_power_kw,
            peak_power_interval_index=peak_interval.interval_index,
            peak_power_timestamp=peak_interval.timestamp,
            total_production_units=total_production,
            overall_energy_intensity_kwh_per_unit=energy_intensity,
        )

    @staticmethod
    def calculate_zone_metrics(
        intervals: List[TimeSeriesInterval],
        zones_config: List[ProductionZoneConfig],
        total_factory_demand_kwh: float,
    ) -> List[ZoneMetric]:
        """Calculate per-zone energy consumption, production, and energy intensity."""
        zone_metrics: List[ZoneMetric] = []

        for zone_cfg in zones_config:
            zid = zone_cfg.zone_id
            zone_readings = [
                next((z for z in interval.zones if z.zone_id == zid), None)
                for interval in intervals
            ]
            valid_readings = [z for z in zone_readings if z is not None]

            if not valid_readings:
                continue

            zone_total_kwh = round(sum(z.energy_kwh for z in valid_readings), 2)
            zone_avg_power_kw = round(sum(z.power_kw for z in valid_readings) / len(valid_readings), 2)
            zone_peak_power_kw = round(max(z.power_kw for z in valid_readings), 2)
            zone_production_units = round(sum(z.production_units for z in valid_readings), 1)

            pct_of_total = (
                round((zone_total_kwh / total_factory_demand_kwh) * 100.0, 2)
                if total_factory_demand_kwh > 0
                else 0.0
            )

            intensity = (
                round(zone_total_kwh / zone_production_units, 4)
                if zone_production_units > 0
                else None
            )

            zone_metrics.append(
                ZoneMetric(
                    zone_id=zid,
                    zone_name=zone_cfg.name,
                    total_consumption_kwh=zone_total_kwh,
                    average_power_kw=zone_avg_power_kw,
                    peak_power_kw=zone_peak_power_kw,
                    percentage_of_total_demand=pct_of_total,
                    total_production_units=zone_production_units,
                    energy_intensity_kwh_per_unit=intensity,
                )
            )

        return zone_metrics

    @staticmethod
    def calculate_shift_metrics(
        intervals: List[TimeSeriesInterval],
        shifts_config: List[ShiftSchedule],
        total_factory_demand_kwh: float,
    ) -> List[ShiftMetric]:
        """Aggregate energy and production metrics across operational shifts."""
        shift_metrics: List[ShiftMetric] = []

        for shift in shifts_config:
            matching = [
                i for i in intervals if shift.start_hour <= i.interval_index < shift.end_hour
            ]
            hours_count = len(matching)
            if hours_count == 0:
                continue

            shift_consumption_kwh = round(sum(i.total_factory_energy_demand_kwh for i in matching), 2)
            shift_production = round(sum(i.actual_production_output_units for i in matching), 1)
            avg_demand_kw = round(shift_consumption_kwh / hours_count, 2)

            pct_share = (
                round((shift_consumption_kwh / total_factory_demand_kwh) * 100.0, 2)
                if total_factory_demand_kwh > 0
                else 0.0
            )

            shift_metrics.append(
                ShiftMetric(
                    shift_name=shift.shift_name,
                    hours_count=hours_count,
                    total_consumption_kwh=shift_consumption_kwh,
                    average_demand_kw=avg_demand_kw,
                    percentage_of_total_demand=pct_share,
                    total_production_units=shift_production,
                )
            )

        return shift_metrics

    @staticmethod
    def calculate_renewable_availability(
        intervals: List[TimeSeriesInterval],
        profile: FactoryProfile,
        total_demand_kwh: float,
    ) -> RenewableAvailabilityMetrics:
        """Calculate separate availability metrics for solar, wind, and biomass."""
        total_hours = len(intervals)

        # Solar PV metrics
        solar_total_kwh = round(sum(i.generation.solar_energy_kwh for i in intervals), 2)
        solar_avg_kw = round(solar_total_kwh / total_hours, 2) if total_hours > 0 else 0.0
        solar_peak_kw = round(max(i.generation.solar_power_kw for i in intervals), 2)
        solar_cap_kw = profile.solar.installed_capacity_kw
        solar_cf = (
            round((solar_total_kwh / (solar_cap_kw * total_hours)) * 100.0, 2)
            if solar_cap_kw > 0 and total_hours > 0
            else 0.0
        )

        # Wind metrics
        wind_total_kwh = round(sum(i.generation.wind_energy_kwh for i in intervals), 2)
        wind_avg_kw = round(wind_total_kwh / total_hours, 2) if total_hours > 0 else 0.0
        wind_peak_kw = round(max(i.generation.wind_power_kw for i in intervals), 2)
        wind_cap_kw = profile.wind.installed_capacity_kw
        wind_cf = (
            round((wind_total_kwh / (wind_cap_kw * total_hours)) * 100.0, 2)
            if wind_cap_kw > 0 and total_hours > 0
            else 0.0
        )

        # Biomass metrics
        biomass_total_kwh = round(sum(i.generation.biomass_max_energy_kwh for i in intervals), 2)
        biomass_avg_kw = round(biomass_total_kwh / total_hours, 2) if total_hours > 0 else 0.0
        biomass_peak_kw = round(max(i.generation.biomass_max_power_kw for i in intervals), 2)
        biomass_cap_kw = profile.biomass.installed_capacity_kw
        biomass_cf = (
            round((biomass_total_kwh / (biomass_cap_kw * total_hours)) * 100.0, 2)
            if biomass_cap_kw > 0 and total_hours > 0
            else 0.0
        )

        sources = [
            RenewableSourceAvailability(
                source="solar",
                total_available_kwh=solar_total_kwh,
                average_available_kw=solar_avg_kw,
                peak_available_kw=solar_peak_kw,
                installed_capacity_kw=solar_cap_kw,
                capacity_factor_percent=solar_cf,
            ),
            RenewableSourceAvailability(
                source="wind",
                total_available_kwh=wind_total_kwh,
                average_available_kw=wind_avg_kw,
                peak_available_kw=wind_peak_kw,
                installed_capacity_kw=wind_cap_kw,
                capacity_factor_percent=wind_cf,
            ),
            RenewableSourceAvailability(
                source="biomass",
                total_available_kwh=biomass_total_kwh,
                average_available_kw=biomass_avg_kw,
                peak_available_kw=biomass_peak_kw,
                installed_capacity_kw=biomass_cap_kw,
                capacity_factor_percent=biomass_cf,
            ),
        ]

        total_renewable_kwh = round(solar_total_kwh + wind_total_kwh + biomass_total_kwh, 2)
        avail_ratio = (
            round((total_renewable_kwh / total_demand_kwh) * 100.0, 2)
            if total_demand_kwh > 0
            else 0.0
        )

        return RenewableAvailabilityMetrics(
            sources=sources,
            total_renewable_available_kwh=total_renewable_kwh,
            availability_to_demand_ratio_percent=avail_ratio,
        )

    @staticmethod
    def calculate_grid_cost_baseline(
        intervals: List[TimeSeriesInterval], grid_config: GridConfig
    ) -> GridCostBaseline:
        """Calculate reference 100% grid-supplied electricity cost under ToD tariffs."""
        period_buckets: Dict[str, Dict[str, float]] = {}

        total_cost_inr = 0.0
        total_energy_kwh = 0.0
        max_demand_kw = 0.0

        for item in intervals:
            kwh = item.total_factory_energy_demand_kwh
            kw = item.total_factory_demand_kw
            rate = item.grid.tariff_rate_inr_per_kwh
            period_name = item.grid.tariff_period_name

            interval_cost = round(kwh * rate, 2)
            total_cost_inr += interval_cost
            total_energy_kwh += kwh
            if kw > max_demand_kw:
                max_demand_kw = kw

            if period_name not in period_buckets:
                period_buckets[period_name] = {
                    "hours_count": 0.0,
                    "tariff_rate": rate,
                    "energy_kwh": 0.0,
                    "cost_inr": 0.0,
                }
            period_buckets[period_name]["hours_count"] += 1.0
            period_buckets[period_name]["energy_kwh"] += kwh
            period_buckets[period_name]["cost_inr"] += interval_cost

        total_cost_inr = round(total_cost_inr, 2)
        total_energy_kwh = round(total_energy_kwh, 2)

        blended_rate = (
            round(total_cost_inr / total_energy_kwh, 2) if total_energy_kwh > 0 else 0.0
        )

        period_breakdown: List[TariffPeriodCost] = []
        for pname, pdata in period_buckets.items():
            pct = round((pdata["cost_inr"] / total_cost_inr) * 100.0, 2) if total_cost_inr > 0 else 0.0
            period_breakdown.append(
                TariffPeriodCost(
                    period_name=pname,
                    tariff_rate_inr_per_kwh=pdata["tariff_rate"],
                    hours_count=int(pdata["hours_count"]),
                    energy_demand_kwh=round(pdata["energy_kwh"], 2),
                    estimated_cost_inr=round(pdata["cost_inr"], 2),
                    percentage_of_total_cost=pct,
                )
            )

        contract_demand = grid_config.contract_demand_kw
        exceeds_cap = max_demand_kw > contract_demand
        headroom = round(contract_demand - max_demand_kw, 2)

        return GridCostBaseline(
            total_estimated_cost_inr=total_cost_inr,
            average_blended_rate_inr_per_kwh=blended_rate,
            period_breakdown=period_breakdown,
            grid_contract_demand_kw=contract_demand,
            max_demand_kw=max_demand_kw,
            exceeds_grid_capacity=exceeds_cap,
            capacity_headroom_kw=headroom,
        )

    @staticmethod
    def calculate_production_analysis(intervals: List[TimeSeriesInterval]) -> ProductionAnalysis:
        """Identify intervals with zero production and calculate non-productive energy."""
        total_production = round(sum(i.actual_production_output_units for i in intervals), 1)

        idle_intervals: List[int] = []
        idle_energy_kwh = 0.0

        for item in intervals:
            if item.actual_production_output_units == 0.0:
                idle_intervals.append(item.interval_index)
                idle_energy_kwh += item.total_factory_energy_demand_kwh

        return ProductionAnalysis(
            total_production_units=total_production,
            idle_or_unproductive_intervals=idle_intervals,
            idle_consumption_total_kwh=round(idle_energy_kwh, 2),
        )

    @classmethod
    def get_energy_metrics_summary(
        cls, factory_id: str = DEFAULT_FACTORY_ID
    ) -> EnergyMetricsSummaryResponse:
        """Compile complete energy metrics summary from cached factory data service."""
        profile_resp = factory_data_service.get_profile(factory_id)
        timeseries_resp = factory_data_service.get_timeseries(factory_id)
        raw_profile = factory_data_service.get_raw_profile(factory_id)
        intervals = timeseries_resp.intervals

        demand_metrics = cls.calculate_demand_metrics(intervals)
        zone_metrics = cls.calculate_zone_metrics(
            intervals, profile_resp.zones, demand_metrics.total_demand_kwh
        )
        shift_metrics = cls.calculate_shift_metrics(
            intervals, profile_resp.shifts, demand_metrics.total_demand_kwh
        )
        renewables = cls.calculate_renewable_availability(
            intervals, raw_profile, demand_metrics.total_demand_kwh
        )
        cost_baseline = cls.calculate_grid_cost_baseline(intervals, profile_resp.grid)
        prod_analysis = cls.calculate_production_analysis(intervals)

        return EnergyMetricsSummaryResponse(
            factory_id=profile_resp.factory_id,
            factory_name=profile_resp.name,
            simulation_date=timeseries_resp.simulation_date,
            demand_metrics=demand_metrics,
            zone_metrics=zone_metrics,
            shift_metrics=shift_metrics,
            renewable_availability=renewables,
            grid_cost_baseline=cost_baseline,
            production_analysis=prod_analysis,
            simulation_metadata=profile_resp.simulation_metadata,
        )

    @classmethod
    def get_energy_profile(
        cls, factory_id: str = DEFAULT_FACTORY_ID
    ) -> AnalyticalEnergyProfileResponse:
        """Build 24-hour analytical time series with costs, renewable availability, and indicators."""
        profile_resp = factory_data_service.get_profile(factory_id)
        timeseries_resp = factory_data_service.get_timeseries(factory_id)
        intervals = timeseries_resp.intervals

        hourly_items: List[HourlyAnalyticalProfileItem] = []
        total_cost_inr = 0.0
        total_demand_kwh = 0.0
        total_prod_units = 0.0
        total_renewables_kwh = 0.0

        for i in intervals:
            cost = round(i.total_factory_energy_demand_kwh * i.grid.tariff_rate_inr_per_kwh, 2)
            total_cost_inr += cost
            total_demand_kwh += i.total_factory_energy_demand_kwh
            total_prod_units += i.actual_production_output_units
            total_renewables_kwh += i.generation.total_renewable_available_kwh

            intensity = (
                round(i.total_factory_energy_demand_kwh / i.actual_production_output_units, 4)
                if i.actual_production_output_units > 0
                else None
            )

            hourly_items.append(
                HourlyAnalyticalProfileItem(
                    interval_index=i.interval_index,
                    timestamp=i.timestamp,
                    factory_demand_kw=i.total_factory_demand_kw,
                    factory_demand_kwh=i.total_factory_energy_demand_kwh,
                    production_units=i.actual_production_output_units,
                    energy_intensity_kwh_per_unit=intensity,
                    solar_available_kwh=i.generation.solar_energy_kwh,
                    wind_available_kwh=i.generation.wind_energy_kwh,
                    biomass_available_kwh=i.generation.biomass_max_energy_kwh,
                    total_renewable_available_kwh=i.generation.total_renewable_available_kwh,
                    grid_tariff_inr_per_kwh=i.grid.tariff_rate_inr_per_kwh,
                    grid_cost_baseline_inr=cost,
                    active_anomalies=i.metadata.active_anomaly_ids,
                    is_peak_tariff=i.grid.is_peak_tariff_period,
                    shift_name=i.metadata.shift_name,
                    is_production_active=i.metadata.is_production_active,
                )
            )

        summary_totals = {
            "total_factory_demand_kwh": round(total_demand_kwh, 2),
            "total_production_units": round(total_prod_units, 1),
            "total_renewable_available_kwh": round(total_renewables_kwh, 2),
            "total_grid_cost_baseline_inr": round(total_cost_inr, 2),
        }

        return AnalyticalEnergyProfileResponse(
            factory_id=profile_resp.factory_id,
            factory_name=profile_resp.name,
            simulation_date=timeseries_resp.simulation_date,
            total_intervals=len(hourly_items),
            hourly_profile=hourly_items,
            summary_totals=summary_totals,
            simulation_metadata=profile_resp.simulation_metadata,
        )


energy_metrics_service = EnergyMetricsService()

