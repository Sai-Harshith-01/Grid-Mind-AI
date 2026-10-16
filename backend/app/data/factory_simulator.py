"""Deterministic synthetic factory data simulation engine.

Generates realistic 24-hour industrial energy and production profiles
with predictable, repeatable anomalies for MSME factories.

IMPORTANT:
This data is purely synthetic and generated for software simulation.
It must never be presented as measured telemetry from real industrial assets.
"""

import math
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple

from app.data.factory_config import FactoryProfile, get_default_factory_profile
from app.schemas.factory import (
    AnomalyScenario,
    AnomalyScenariosResponse,
    FactoryOverviewResponse,
    FactoryProfileResponse,
    FactoryTimeSeriesResponse,
    GenerationAvailability,
    GridData,
    IntervalMetadata,
    MachineReading,
    RenewableAvailabilitySummary,
    DemandIntervalSummary,
    SimulationMetadata,
    TimeSeriesInterval,
    ZoneReading,
)


class FactorySimulator:
    """Deterministic simulation engine generating 24-hour factory intervals and anomalies."""

    def __init__(
        self,
        profile: FactoryProfile | None = None,
        seed: int = 42,
        simulation_date: str = "2026-10-14",
    ):
        self.profile = profile or get_default_factory_profile()
        self.seed = seed
        self.simulation_date = simulation_date
        self.tz = timezone(timedelta(hours=5, minutes=30))  # Indian Standard Time (IST)

    def _get_active_shift(self, hour: int):
        """Identify which shift is active for a given hour."""
        for shift in self.profile.shifts:
            if shift.start_hour <= hour < shift.end_hour:
                return shift
        return self.profile.shifts[-1]

    def _get_grid_tariff(self, hour: int) -> Tuple[float, str, bool]:
        """Return (rate_inr_per_kwh, period_name, is_peak) for the given hour."""
        for period in self.profile.grid.tariffs:
            if hour in period.hours:
                is_peak = "Peak" in period.period_name
                return period.rate_inr_per_kwh, period.period_name, is_peak
        # Default fallback
        return 8.20, "Normal / Day", False

    def _calculate_solar_availability(self, hour: int, rng: random.Random) -> float:
        """Simulate daylight solar generation curve in kW for a 100 kWp rooftop plant."""
        # Solar radiation between 06:00 and 18:00
        if hour < 6 or hour >= 18:
            return 0.0

        # Daylight span 6:00 to 18:00 (12 hours), peak around 12:30
        daylight_progress = (hour - 6.0) / 12.0
        # Sine curve for solar irradiance
        solar_fraction = math.sin(daylight_progress * math.pi)

        # Base generation with slight atmospheric turbulence variation (+/- 4%)
        variation = rng.uniform(0.96, 1.04)
        peak_kw = self.profile.solar.installed_capacity_kw * self.profile.solar.peak_efficiency
        output = peak_kw * solar_fraction * variation

        return max(0.0, min(round(output, 2), self.profile.solar.installed_capacity_kw))

    def _calculate_wind_availability(self, hour: int, rng: random.Random) -> float:
        """Simulate independent diurnal wind generation in kW for a 60 kW turbine."""
        # Realistic diurnal pattern: breezier at night/early morning and dusk, calmer in early afternoon
        diurnal_weights = [
            0.55, 0.58, 0.62, 0.65, 0.60, 0.52,  # 00:00 - 05:00
            0.45, 0.40, 0.35, 0.32, 0.28, 0.25,  # 06:00 - 11:00
            0.22, 0.24, 0.28, 0.35, 0.45, 0.55,  # 12:00 - 17:00
            0.68, 0.72, 0.65, 0.58, 0.54, 0.52,  # 18:00 - 23:00
        ]
        base_fraction = diurnal_weights[hour]
        variation = rng.uniform(0.92, 1.08)
        output = self.profile.wind.installed_capacity_kw * base_fraction * variation

        return max(0.0, min(round(output, 2), self.profile.wind.installed_capacity_kw))

    def _calculate_biomass_availability(
        self, hour: int, cumulative_biomass_kwh: float, rng: random.Random
    ) -> float:
        """Simulate dispatchable biomass generation capacity in kW within fuel limits."""
        daily_max_kwh = self.profile.biomass.daily_energy_capacity_kwh
        remaining_fuel_kwh = max(0.0, daily_max_kwh - cumulative_biomass_kwh)

        # Biomass generator can deliver up to installed capacity (50 kW) if fuel remains
        max_deliverable_kw = min(self.profile.biomass.installed_capacity_kw, remaining_fuel_kwh)
        # Steady availability factor (95-100% of capacity available on demand)
        availability = max_deliverable_kw * rng.uniform(0.95, 1.0)

        return max(0.0, min(round(availability, 2), self.profile.biomass.installed_capacity_kw))

    def get_anomaly_scenarios(self) -> List[AnomalyScenario]:
        """Return the pre-defined reproducible anomaly scenarios."""
        dt_base = datetime.strptime(self.simulation_date, "%Y-%m-%d").replace(tzinfo=self.tz)

        return [
            AnomalyScenario(
                scenario_id="ANOMALY_IDLE_WASTE_001",
                category="idle_machine_waste",
                title="Off-Shift Furnace Heating Idle Waste",
                interval_index=3,
                timestamp=(dt_base + timedelta(hours=3)).isoformat(),
                affected_zone_id="zone_heat_treatment",
                affected_machine_id="IND_FURNACE_01",
                expected_baseline_value=6.5,
                observed_simulated_value=48.0,
                unit="kWh",
                difference_value=41.5,
                severity="medium",
                reason=(
                    "Induction hardening furnace pre-heat elements and auxiliary cooling water pumps "
                    "were inadvertently left active during the scheduled off-shift maintenance period (00:00 - 08:00)."
                ),
                suggested_remediation=(
                    "Implement automated off-shift lockout on furnace PLC controllers to enforce standby power."
                ),
            ),
            AnomalyScenario(
                scenario_id="ANOMALY_CONSUMPTION_SPIKE_002",
                category="unexpected_consumption_spike",
                title="Pneumatic Ring Main Leakage & Compressor Overload",
                interval_index=11,
                timestamp=(dt_base + timedelta(hours=11)).isoformat(),
                affected_zone_id="zone_cnc",
                affected_machine_id="COMP_AIR_01",
                expected_baseline_value=68.0,
                observed_simulated_value=105.0,
                unit="kWh",
                difference_value=37.0,
                severity="high",
                reason=(
                    "Pneumatic ring-main seal rupture and pressure-relief solenoid malfunction in Zone 1 "
                    "caused the 30 kW compressor to run continuously at 100% full-load unloader bypass."
                ),
                suggested_remediation=(
                    "Service air ring isolation valve and inspect line pressure transducer calibration."
                ),
            ),
            AnomalyScenario(
                scenario_id="ANOMALY_PEAK_THRESHOLD_003",
                category="high_demand_period",
                title="Peak Tariff Window Demand Surge Approaching Sanctioned Limit",
                interval_index=19,
                timestamp=(dt_base + timedelta(hours=19)).isoformat(),
                affected_zone_id="facility_total",
                affected_machine_id=None,
                expected_baseline_value=145.0,
                observed_simulated_value=238.5,
                unit="kW",
                difference_value=93.5,
                severity="critical",
                reason=(
                    "Concurrent shift handover, furnace reheating, and uncoordinated motor starting caused "
                    "factory demand to surge to 238.5 kW, approaching the 250 kW contract demand sanction limit "
                    "(95.4%) during the highest Time-of-Day (ToD) tariff window (INR 11.80/kWh)."
                ),
                suggested_remediation=(
                    "Schedule furnace preheating outside the 18:00-22:00 peak tariff window and stagger motor starts."
                ),
            ),
        ]

    def generate_timeseries(self) -> List[TimeSeriesInterval]:
        """Generate deterministic 24-hour time series intervals with repeatable anomalies."""
        rng = random.Random(self.seed)
        dt_base = datetime.strptime(self.simulation_date, "%Y-%m-%d").replace(tzinfo=self.tz)
        intervals: List[TimeSeriesInterval] = []

        cumulative_biomass_kwh = 0.0

        for hour in range(24):
            interval_timestamp = (dt_base + timedelta(hours=hour)).isoformat()
            shift = self._get_active_shift(hour)
            tariff_rate, tariff_period_name, is_peak_tariff = self._get_grid_tariff(hour)

            zone_readings: List[ZoneReading] = []
            total_active_production_units = 0.0
            total_machines_power_kw = 0.0

            # Generate reading for each zone
            for zone in self.profile.zones:
                is_zone_active = zone.zone_id in shift.active_zones
                machine_readings: List[MachineReading] = []
                zone_power_kw = 0.0

                for machine in zone.machines:
                    if is_zone_active:
                        # Active production range with subtle deterministic jitter (+/- 2%)
                        min_p, max_p = machine.active_power_range_kw
                        base_p = min_p + (max_p - min_p) * shift.production_target_multiplier
                        power = base_p * rng.uniform(0.98, 1.02)
                        is_machine_active = True
                    else:
                        # Idle standby power
                        power = machine.idle_power_kw * rng.uniform(0.97, 1.03)
                        is_machine_active = False

                    # Check for Anomaly 1: Idle Waste in Zone 2 Furnace at Hour 3
                    if hour == 3 and machine.machine_id == "IND_FURNACE_01":
                        power = 42.0  # Injected furnace surge during off-shift
                        is_machine_active = True
                    elif hour == 3 and machine.machine_id == "QUENCH_PUMP_01":
                        power = 6.0  # Auxiliary cooling pump running

                    # Check for Anomaly 2: Compressor overload in Zone 1 at Hour 11
                    if hour == 11 and machine.machine_id == "COMP_AIR_01":
                        power = 30.0  # Full load continuous
                    elif hour == 11 and zone.zone_id == "zone_cnc":
                        # CNC machines worked at elevated load (37.5 kW each) due to pneumatic pressure drops
                        power = 37.5

                    # Check for Anomaly 3: Concurrent shift handover, furnace reheating, and uncoordinated motor surge at Hour 19
                    if hour == 19:
                        if machine.machine_id == "CNC_VMC_01":
                            power = 42.0
                            is_machine_active = True
                        elif machine.machine_id == "CNC_VMC_02":
                            power = 42.0
                            is_machine_active = True
                        elif machine.machine_id == "COMP_AIR_01":
                            power = 30.0
                            is_machine_active = True
                        elif machine.machine_id == "IND_FURNACE_01":
                            power = 68.0  # Reheating surge
                            is_machine_active = True
                        elif machine.machine_id == "QUENCH_PUMP_01":
                            power = 12.0
                            is_machine_active = True
                        elif machine.machine_id == "GRIND_DEBURR_01":
                            power = 24.5
                            is_machine_active = True
                        elif machine.machine_id == "INSPECT_PACK_01":
                            power = 10.0
                            is_machine_active = True

                    power = round(power, 2)
                    energy = round(power * 1.0, 2)  # 1 hour duration
                    machine_readings.append(
                        MachineReading(
                            machine_id=machine.machine_id,
                            name=machine.name,
                            power_kw=power,
                            energy_kwh=energy,
                            is_active=is_machine_active,
                        )
                    )
                    zone_power_kw += power

                # Production output for this zone
                if is_zone_active or (hour == 19 and zone.zone_id == "zone_heat_treatment"):
                    zone_units = round(
                        zone.max_production_capacity_units_per_hour
                        * shift.production_target_multiplier
                        * rng.uniform(0.95, 0.99),
                        1,
                    )
                else:
                    zone_units = 0.0

                zone_power_kw = round(zone_power_kw, 2)
                zone_energy_kwh = round(zone_power_kw * 1.0, 2)
                zone_readings.append(
                    ZoneReading(
                        zone_id=zone.zone_id,
                        zone_name=zone.name,
                        power_kw=zone_power_kw,
                        energy_kwh=zone_energy_kwh,
                        production_units=zone_units,
                        is_active=is_zone_active or (hour == 19 and zone.zone_id == "zone_heat_treatment"),
                        machines=machine_readings,
                    )
                )
                total_machines_power_kw += zone_power_kw
                total_active_production_units += zone_units

            # Facility baseload (unaffected by shifts: lighting, server, security)
            if hour == 19:
                facility_baseload_kw = 10.0
            else:
                facility_baseload_kw = round(self.profile.facility_baseload_kw * rng.uniform(0.98, 1.02), 2)
            facility_baseload_kwh = round(facility_baseload_kw * 1.0, 2)

            total_factory_demand_kw = round(total_machines_power_kw + facility_baseload_kw, 2)

            # Injected Anomaly 3: Peak Demand Surge at Hour 19
            active_anomalies: List[str] = []
            if hour == 3:
                active_anomalies.append("ANOMALY_IDLE_WASTE_001")
            elif hour == 11:
                active_anomalies.append("ANOMALY_CONSUMPTION_SPIKE_002")
            elif hour == 19:
                active_anomalies.append("ANOMALY_PEAK_THRESHOLD_003")

            total_factory_energy_demand_kwh = round(total_factory_demand_kw * 1.0, 2)

            # Renewable generation availability
            solar_kw = self._calculate_solar_availability(hour, rng)
            solar_kwh = round(solar_kw * 1.0, 2)

            wind_kw = self._calculate_wind_availability(hour, rng)
            wind_kwh = round(wind_kw * 1.0, 2)

            biomass_kw = self._calculate_biomass_availability(hour, cumulative_biomass_kwh, rng)
            biomass_kwh = round(biomass_kw * 1.0, 2)
            cumulative_biomass_kwh += biomass_kwh

            total_renewable_available_kwh = round(solar_kwh + wind_kwh + biomass_kwh, 2)

            # Production demand calculation
            base_target = 220.0 * shift.production_target_multiplier
            production_demand_units = round(base_target, 1)

            intervals.append(
                TimeSeriesInterval(
                    interval_index=hour,
                    timestamp=interval_timestamp,
                    interval_duration_hours=1.0,
                    production_demand_units=production_demand_units,
                    actual_production_output_units=round(total_active_production_units, 1),
                    total_factory_demand_kw=total_factory_demand_kw,
                    total_factory_energy_demand_kwh=total_factory_energy_demand_kwh,
                    facility_baseload_kwh=facility_baseload_kwh,
                    zones=zone_readings,
                    generation=GenerationAvailability(
                        solar_power_kw=solar_kw,
                        solar_energy_kwh=solar_kwh,
                        wind_power_kw=wind_kw,
                        wind_energy_kwh=wind_kwh,
                        biomass_max_power_kw=biomass_kw,
                        biomass_max_energy_kwh=biomass_kwh,
                        total_renewable_available_kwh=total_renewable_available_kwh,
                    ),
                    grid=GridData(
                        tariff_rate_inr_per_kwh=tariff_rate,
                        tariff_period_name=tariff_period_name,
                        supply_capacity_kw=self.profile.grid.contract_demand_kw,
                        is_peak_tariff_period=is_peak_tariff,
                    ),
                    metadata=IntervalMetadata(
                        shift_name=shift.shift_name,
                        is_production_active=len(shift.active_zones) > 0,
                        active_anomaly_ids=active_anomalies,
                    ),
                )
            )

        self._validate_timeseries(intervals)
        return intervals

    def _validate_timeseries(self, intervals: List[TimeSeriesInterval]) -> None:
        """Enforce strict integrity constraints on the generated time series."""
        if len(intervals) != 24:
            raise ValueError(f"Expected exactly 24 intervals, got {len(intervals)}")

        timestamps = [item.timestamp for item in intervals]
        if len(set(timestamps)) != 24:
            raise ValueError("Timestamps must be unique across all 24 intervals.")

        solar_cap = self.profile.solar.installed_capacity_kw
        wind_cap = self.profile.wind.installed_capacity_kw
        biomass_cap = self.profile.biomass.installed_capacity_kw

        for idx, item in enumerate(intervals):
            if item.interval_index != idx:
                raise ValueError(f"Interval index mismatch: expected {idx}, got {item.interval_index}")
            if item.total_factory_demand_kw < 0 or item.total_factory_energy_demand_kwh < 0:
                raise ValueError(f"Interval {idx} contains negative factory demand.")
            if item.actual_production_output_units < 0:
                raise ValueError(f"Interval {idx} contains negative production output.")

            gen = item.generation
            if gen.solar_power_kw < 0 or gen.solar_power_kw > solar_cap + 0.01:
                raise ValueError(f"Interval {idx} solar {gen.solar_power_kw}kW exceeds capacity {solar_cap}kW.")
            if gen.wind_power_kw < 0 or gen.wind_power_kw > wind_cap + 0.01:
                raise ValueError(f"Interval {idx} wind {gen.wind_power_kw}kW exceeds capacity {wind_cap}kW.")
            if gen.biomass_max_power_kw < 0 or gen.biomass_max_power_kw > biomass_cap + 0.01:
                raise ValueError(f"Interval {idx} biomass {gen.biomass_max_power_kw}kW exceeds capacity {biomass_cap}kW.")

            # Solar daylight constraint: must be 0 between 00:00 and 05:00, and after 18:00
            if (idx < 6 or idx >= 18) and gen.solar_power_kw > 0.0:
                raise ValueError(f"Night interval {idx} cannot produce solar energy.")

            if item.grid.tariff_rate_inr_per_kwh <= 0:
                raise ValueError(f"Interval {idx} tariff must be positive.")
            if item.grid.supply_capacity_kw <= 0:
                raise ValueError(f"Interval {idx} grid capacity must be positive.")

    def generate_overview(self, intervals: List[TimeSeriesInterval]) -> FactoryOverviewResponse:
        """Derive descriptive metrics from the generated time series."""
        total_demand_kwh = round(sum(i.total_factory_energy_demand_kwh for i in intervals), 2)
        total_production = round(sum(i.actual_production_output_units for i in intervals), 1)

        avg_intensity = (
            round(total_demand_kwh / total_production, 3) if total_production > 0 else 0.0
        )

        total_solar_kwh = round(sum(i.generation.solar_energy_kwh for i in intervals), 2)
        total_wind_kwh = round(sum(i.generation.wind_energy_kwh for i in intervals), 2)
        total_biomass_kwh = round(sum(i.generation.biomass_max_energy_kwh for i in intervals), 2)
        total_renewable_kwh = round(total_solar_kwh + total_wind_kwh + total_biomass_kwh, 2)

        # Find highest and lowest demand intervals
        highest = max(intervals, key=lambda i: i.total_factory_demand_kw)
        lowest = min(intervals, key=lambda i: i.total_factory_demand_kw)

        grid_capacity = self.profile.grid.contract_demand_kw
        peak_ratio = round((highest.total_factory_demand_kw / grid_capacity) * 100.0, 2)

        anomalies = self.get_anomaly_scenarios()

        return FactoryOverviewResponse(
            factory_id=self.profile.factory_id,
            factory_name=self.profile.name,
            simulation_date=self.simulation_date,
            total_intervals=len(intervals),
            total_factory_energy_demand_kwh=total_demand_kwh,
            total_production_units=total_production,
            average_energy_intensity_kwh_per_unit=avg_intensity,
            renewable_energy_availability=RenewableAvailabilitySummary(
                solar_total_kwh=total_solar_kwh,
                wind_total_kwh=total_wind_kwh,
                biomass_available_total_kwh=total_biomass_kwh,
                total_renewable_available_kwh=total_renewable_kwh,
            ),
            highest_demand_interval=DemandIntervalSummary(
                interval_index=highest.interval_index,
                timestamp=highest.timestamp,
                demand_kw=highest.total_factory_demand_kw,
                demand_kwh=highest.total_factory_energy_demand_kwh,
                grid_tariff_inr_per_kwh=highest.grid.tariff_rate_inr_per_kwh,
            ),
            lowest_demand_interval=DemandIntervalSummary(
                interval_index=lowest.interval_index,
                timestamp=lowest.timestamp,
                demand_kw=lowest.total_factory_demand_kw,
                demand_kwh=lowest.total_factory_energy_demand_kwh,
                grid_tariff_inr_per_kwh=lowest.grid.tariff_rate_inr_per_kwh,
            ),
            grid_contract_demand_kw=grid_capacity,
            peak_demand_to_capacity_ratio_percent=peak_ratio,
            total_anomalies_count=len(anomalies),
            simulation_metadata=SimulationMetadata(
                simulation_seed=self.seed,
                simulation_date=self.simulation_date,
            ),
        )
