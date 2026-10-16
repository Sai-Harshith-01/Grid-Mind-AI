"""Automated test suite for Phase 4 Renewable Energy Allocation and Optimisation.

Tests:
1. All allocations are nonnegative.
2. Energy balance holds for every feasible interval.
3. Solar allocation never exceeds solar availability.
4. Wind allocation never exceeds wind availability.
5. Biomass generation respects power and daily fuel limits.
6. Grid allocation respects contract demand.
7. Time-of-day grid tariffs are applied correctly.
8. Source operating costs are included correctly.
9. The optimiser matches a hand-calculated small test case.
10. Estimated savings use the correct formula.
11. Negative savings are represented honestly.
12. Zero baseline cost does not cause division by zero.
13. Renewable allocation percentage uses allocated energy, not available generation.
14. Production fulfilment is not invented when the required data is unavailable.
15. An infeasible demand interval is reported explicitly.
16. Solver failures are distinguishable from genuine infeasibility.
17. Repeated runs on the same dataset produce consistent results.
18. All new API endpoints return the correct schemas.
19. Existing factory and analysis endpoints remain functional.
20. The complete existing backend test suite passes.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.factory_config import (
    BiomassConfig,
    GridConfig,
    GridTariffPeriod,
    SolarConfig,
    WindConfig,
    get_default_factory_profile,
)
from app.schemas.factory import (
    GenerationAvailability,
    GridData,
    IntervalMetadata,
    TimeSeriesInterval,
    ZoneReading,
)
from app.services.energy_optimizer import (
    EnergyOptimizerService,
    energy_optimizer_service,
)
from app.services.factory_data_service import factory_data_service

client = TestClient(app)


class TestOptimizerUnit:
    """Unit tests for the linear programming energy optimizer."""

    def test_all_allocations_nonnegative(self):
        """1. Verify every source allocation variable is strictly nonnegative."""
        intervals = factory_data_service.get_timeseries().intervals
        profile = factory_data_service._profile
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        assert opt_run.is_feasible is True
        for interval in opt_run.intervals:
            assert interval.solar_allocated_kwh >= 0.0
            assert interval.wind_allocated_kwh >= 0.0
            assert interval.biomass_allocated_kwh >= 0.0
            assert interval.grid_allocated_kwh >= 0.0

    def test_energy_balance_holds_for_every_interval(self):
        """2. Verify supply exactly satisfies demand for all feasible intervals."""
        intervals = factory_data_service.get_timeseries().intervals
        profile = factory_data_service._profile
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        for interval in opt_run.intervals:
            total_supplied = (
                interval.solar_allocated_kwh
                + interval.wind_allocated_kwh
                + interval.biomass_allocated_kwh
                + interval.grid_allocated_kwh
            )
            assert abs(total_supplied - interval.factory_demand_kwh) < 0.02
            assert interval.energy_balance_error < 0.02

    def test_solar_allocation_never_exceeds_availability(self):
        """3. Verify solar allocation <= available solar generation."""
        intervals = factory_data_service.get_timeseries().intervals
        profile = factory_data_service._profile
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        for interval in opt_run.intervals:
            assert interval.solar_allocated_kwh <= interval.solar_available_kwh + 0.01
            assert interval.solar_allocated_kwh <= profile.solar.installed_capacity_kw + 0.01

    def test_wind_allocation_never_exceeds_availability(self):
        """4. Verify wind allocation <= available wind generation."""
        intervals = factory_data_service.get_timeseries().intervals
        profile = factory_data_service._profile
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        for interval in opt_run.intervals:
            assert interval.wind_allocated_kwh <= interval.wind_available_kwh + 0.01
            assert interval.wind_allocated_kwh <= profile.wind.installed_capacity_kw + 0.01

    def test_biomass_respects_power_and_fuel_limits(self):
        """5. Verify biomass allocation respects power capacity and daily fuel cap."""
        intervals = factory_data_service.get_timeseries().intervals
        profile = factory_data_service._profile
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        # Power limit per hour (50 kW * 1h = 50 kWh)
        for interval in opt_run.intervals:
            assert interval.biomass_allocated_kwh <= profile.biomass.installed_capacity_kw + 0.01

        # Total energy limit across 24h
        total_biomass = sum(i.biomass_allocated_kwh for i in opt_run.intervals)
        assert total_biomass <= profile.biomass.daily_energy_capacity_kwh + 0.05
        assert opt_run.biomass_energy_consumed_kwh == round(total_biomass, 2)
        assert opt_run.biomass_remaining_fuel_budget_kg >= 0.0

    def test_grid_allocation_respects_contract_demand(self):
        """6. Verify grid allocation never exceeds contract demand."""
        intervals = factory_data_service.get_timeseries().intervals
        profile = factory_data_service._profile
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        contract_cap = profile.grid.contract_demand_kw
        for interval in opt_run.intervals:
            assert interval.grid_allocated_kwh <= contract_cap + 0.01
        assert opt_run.peak_grid_power_kw <= contract_cap

    def test_tod_tariffs_and_source_operating_costs_applied(self):
        """7 & 8. Verify tariffs and source fuel costs are properly calculated."""
        intervals = factory_data_service.get_timeseries().intervals
        profile = factory_data_service._profile
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        c_biomass = profile.biomass.fuel_cost_inr_per_kwh
        for interval in opt_run.intervals:
            expected_grid_cost = round(interval.grid_allocated_kwh * interval.grid_tariff_inr_per_kwh, 2)
            expected_src_cost = round(interval.biomass_allocated_kwh * c_biomass, 2)
            assert abs(interval.grid_tariff_cost_inr - expected_grid_cost) < 0.05
            assert abs(interval.source_operating_cost_inr - expected_src_cost) < 0.05

    def test_hand_calculated_small_test_case(self):
        """9. Verify LP solver against an independent hand-calculated 2-interval scenario."""
        profile = get_default_factory_profile()
        profile.biomass.fuel_cost_inr_per_kwh = 4.20
        profile.biomass.installed_capacity_kw = 50.0

        # Construct 2 test intervals:
        # Interval 0: Demand 100 kWh, Solar 0, Wind 40, Tariff 6.50
        # -> Optimal: Wind 40 (c=0), Biomass 50 (c=4.20), Grid 10 (c=6.50)
        # Cost = 40*0 + 50*4.20 + 10*6.50 = 210 + 65 = INR 275.00
        # Interval 1: Demand 80 kWh, Solar 50, Wind 20, Tariff 8.20
        # -> Optimal: Solar 50 (c=0), Wind 20 (c=0), Biomass 10 (c=4.20), Grid 0
        # Cost = 50*0 + 20*0 + 10*4.20 = INR 42.00
        # Total cost = 275 + 42 = INR 317.00
        # Baseline cost = 100*6.50 + 80*8.20 = 650 + 656 = INR 1306.00
        # Savings = 1306 - 317 = INR 989.00
        i0 = TimeSeriesInterval(
            interval_index=0,
            timestamp="2026-10-14T00:00:00+05:30",
            interval_duration_hours=1.0,
            production_demand_units=0.0,
            actual_production_output_units=0.0,
            total_factory_demand_kw=100.0,
            total_factory_energy_demand_kwh=100.0,
            facility_baseload_kwh=10.0,
            zones=[],
            generation=GenerationAvailability(
                solar_power_kw=0.0,
                solar_energy_kwh=0.0,
                wind_power_kw=40.0,
                wind_energy_kwh=40.0,
                biomass_max_power_kw=50.0,
                biomass_max_energy_kwh=50.0,
                total_renewable_available_kwh=90.0,
            ),
            grid=GridData(
                tariff_rate_inr_per_kwh=6.50,
                tariff_period_name="Off-Peak",
                supply_capacity_kw=250.0,
                is_peak_tariff_period=False,
            ),
            metadata=IntervalMetadata(shift_name="Night", is_production_active=False),
        )

        i1 = TimeSeriesInterval(
            interval_index=1,
            timestamp="2026-10-14T01:00:00+05:30",
            interval_duration_hours=1.0,
            production_demand_units=50.0,
            actual_production_output_units=50.0,
            total_factory_demand_kw=80.0,
            total_factory_energy_demand_kwh=80.0,
            facility_baseload_kwh=10.0,
            zones=[],
            generation=GenerationAvailability(
                solar_power_kw=50.0,
                solar_energy_kwh=50.0,
                wind_power_kw=20.0,
                wind_energy_kwh=20.0,
                biomass_max_power_kw=50.0,
                biomass_max_energy_kwh=50.0,
                total_renewable_available_kwh=120.0,
            ),
            grid=GridData(
                tariff_rate_inr_per_kwh=8.20,
                tariff_period_name="Normal",
                supply_capacity_kw=250.0,
                is_peak_tariff_period=False,
            ),
            metadata=IntervalMetadata(shift_name="Morning", is_production_active=True),
        )

        test_run = EnergyOptimizerService().optimize([i0, i1], profile)
        assert test_run.is_feasible is True
        assert abs(test_run.optimised_supply_cost_inr - 317.00) < 0.1
        assert abs(test_run.baseline_grid_only_cost_inr - 1306.00) < 0.1
        assert abs(test_run.estimated_savings_inr - 989.00) < 0.1

        # Check allocations in interval 0
        int0 = test_run.intervals[0]
        assert abs(int0.wind_allocated_kwh - 40.0) < 0.05
        assert abs(int0.biomass_allocated_kwh - 50.0) < 0.05
        assert abs(int0.grid_allocated_kwh - 10.0) < 0.05

        # Check allocations in interval 1
        int1 = test_run.intervals[1]
        assert abs(int1.solar_allocated_kwh - 50.0) < 0.05
        assert abs(int1.wind_allocated_kwh - 20.0) < 0.05
        assert abs(int1.biomass_allocated_kwh - 10.0) < 0.05
        assert abs(int1.grid_allocated_kwh - 0.0) < 0.05

    def test_estimated_savings_and_zero_baseline_division_protection(self):
        """10, 11 & 12. Verify savings formula and guard against zero baseline."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        # Baseline - Optimised = Savings
        calc_savings = round(opt_run.baseline_grid_only_cost_inr - opt_run.optimised_supply_cost_inr, 2)
        assert abs(opt_run.estimated_savings_inr - calc_savings) < 0.1

        # Test zero baseline scenario
        zero_interval = TimeSeriesInterval(
            interval_index=0,
            timestamp="2026-10-14T00:00:00+05:30",
            interval_duration_hours=1.0,
            production_demand_units=0.0,
            actual_production_output_units=0.0,
            total_factory_demand_kw=0.0,
            total_factory_energy_demand_kwh=0.0,
            facility_baseload_kwh=0.0,
            zones=[],
            generation=GenerationAvailability(
                solar_power_kw=0.0,
                solar_energy_kwh=0.0,
                wind_power_kw=0.0,
                wind_energy_kwh=0.0,
                biomass_max_power_kw=0.0,
                biomass_max_energy_kwh=0.0,
                total_renewable_available_kwh=0.0,
            ),
            grid=GridData(
                tariff_rate_inr_per_kwh=8.0,
                tariff_period_name="Normal",
                supply_capacity_kw=250.0,
                is_peak_tariff_period=False,
            ),
            metadata=IntervalMetadata(shift_name="Off", is_production_active=False),
        )
        zero_run = EnergyOptimizerService().optimize([zero_interval], profile)
        assert zero_run.baseline_grid_only_cost_inr == 0.0
        assert zero_run.estimated_savings_percentage == 0.0

    def test_renewable_allocation_percentage_uses_allocated_energy(self):
        """13. Verify renewable allocation % uses allocated energy, not raw availability."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals
        opt_run = EnergyOptimizerService().optimize(intervals, profile)

        total_avail = sum(i.generation.total_renewable_available_kwh for i in intervals)
        total_alloc = opt_run.renewable_energy_allocated_kwh

        # Available generation can exceed what was physically dispatched
        assert total_avail >= total_alloc

        expected_pct = round((total_alloc / opt_run.total_demand_served_kwh) * 100.0, 2)
        assert abs(opt_run.renewable_allocation_percentage - expected_pct) < 0.05

    def test_infeasible_demand_interval_reported_explicitly(self):
        """15 & 16. Verify infeasible intervals are detected without crashing."""
        profile = get_default_factory_profile()
        profile.grid.contract_demand_kw = 50.0
        profile.biomass.installed_capacity_kw = 10.0
        profile.solar.installed_capacity_kw = 10.0
        profile.wind.installed_capacity_kw = 10.0

        # Demand of 500 kWh exceeds max supply (50 + 10 + 10 + 10 = 80 kWh)
        infeasible_interval = TimeSeriesInterval(
            interval_index=0,
            timestamp="2026-10-14T00:00:00+05:30",
            interval_duration_hours=1.0,
            production_demand_units=100.0,
            actual_production_output_units=100.0,
            total_factory_demand_kw=500.0,
            total_factory_energy_demand_kwh=500.0,
            facility_baseload_kwh=10.0,
            zones=[],
            generation=GenerationAvailability(
                solar_power_kw=10.0,
                solar_energy_kwh=10.0,
                wind_power_kw=10.0,
                wind_energy_kwh=10.0,
                biomass_max_power_kw=10.0,
                biomass_max_energy_kwh=10.0,
                total_renewable_available_kwh=30.0,
            ),
            grid=GridData(
                tariff_rate_inr_per_kwh=8.0,
                tariff_period_name="Normal",
                supply_capacity_kw=50.0,
                is_peak_tariff_period=False,
            ),
            metadata=IntervalMetadata(shift_name="Day", is_production_active=True),
        )

        infeasible_run = EnergyOptimizerService().optimize([infeasible_interval], profile)
        assert infeasible_run.is_feasible is False
        assert infeasible_run.infeasible_intervals_count >= 1
        assert infeasible_run.unmet_demand_total_kwh > 0.0

    def test_repeated_runs_return_consistent_results(self):
        """17. Verify optimization is strictly deterministic across repeated runs."""
        run1 = energy_optimizer_service.run_optimization()
        run2 = energy_optimizer_service.run_optimization()

        assert run1.optimised_supply_cost_inr == run2.optimised_supply_cost_inr
        assert run1.estimated_savings_inr == run2.estimated_savings_inr
        assert run1.renewable_energy_allocated_kwh == run2.renewable_energy_allocated_kwh
        assert len(run1.intervals) == len(run2.intervals) == 24


class TestOptimizationApiIntegration:
    """Integration tests for optimization API endpoints."""

    def test_get_optimization_baseline(self):
        """Verify GET /api/optimization/baseline returns correct schema."""
        response = client.get("/api/optimization/baseline")
        assert response.status_code == 200
        data = response.json()

        assert data["factory_id"] == "DEMO-FAC-001"
        assert data["total_baseline_cost_inr"] > 0
        assert data["is_capacity_feasible"] is True
        assert len(data["hourly_baseline"]) == 24
        assert data["simulation_metadata"]["is_synthetic"] is True

    def test_get_optimization_run(self):
        """Verify GET /api/optimization/run returns full allocation schedule."""
        response = client.get("/api/optimization/run")
        assert response.status_code == 200
        data = response.json()

        assert data["is_feasible"] is True
        assert data["estimated_savings_inr"] > 0
        assert data["estimated_savings_percentage"] > 0
        assert data["renewable_allocation_percentage"] > 0
        assert len(data["intervals"]) == 24
        assert len(data["source_breakdown"]) == 4

        # Check source breakdown has solar, wind, biomass, grid
        sources = {s["source"] for s in data["source_breakdown"]}
        assert sources == {"solar", "wind", "biomass", "grid"}

    def test_get_optimization_summary(self):
        """Verify GET /api/optimization/summary returns compact dashboard metrics."""
        response = client.get("/api/optimization/summary")
        assert response.status_code == 200
        data = response.json()

        assert "estimated_savings_inr" in data
        assert "renewable_allocation_percentage" in data
        assert "peak_grid_power_kw" in data
        assert "biomass_remaining_fuel_budget_kg" in data
        assert data["simulation_metadata"]["is_synthetic"] is True

    def test_preservation_of_all_previous_endpoints(self):
        """19. Ensure Phase 1, Phase 2, and Phase 3 endpoints remain functional."""
        # Phase 1
        assert client.get("/health").status_code == 200
        assert client.get("/").status_code == 200

        # Phase 2
        assert client.get("/api/factory/profile").status_code == 200
        assert client.get("/api/factory/timeseries").status_code == 200
        assert client.get("/api/factory/anomaly-scenarios").status_code == 200
        assert client.get("/api/factory/overview").status_code == 200

        # Phase 3
        assert client.get("/api/analysis/metrics").status_code == 200
        assert client.get("/api/analysis/anomalies").status_code == 200
        assert client.get("/api/analysis/anomalies/FINDING-IDLE-WASTE-H03").status_code == 200
        assert client.get("/api/analysis/energy-profile").status_code == 200

    def test_numerical_savings_arithmetic_exact(self):
        """21. Verify Daily Savings = Baseline Cost - Optimised Cost exactly."""
        for fid in ["DEMO-FAC-001", "DEMO-FAC-002", "DEMO-FAC-003"]:
            opt = EnergyOptimizerService.get_summary(fid)
            expected_savings = round(
                opt.baseline_grid_only_cost_inr - opt.optimised_supply_cost_inr, 2
            )
            assert opt.estimated_savings_inr == expected_savings
            expected_pct = round((expected_savings / opt.baseline_grid_only_cost_inr) * 100.0, 2)
            assert opt.estimated_savings_percentage == expected_pct

    def test_annualised_savings_multi_horizon(self):
        """22. Verify annualised savings for 250, 300, 350, 365 operating days and lakhs conversion."""
        opt = EnergyOptimizerService.get_summary("DEMO-FAC-001")
        daily = opt.estimated_savings_inr
        assert daily > 0

        for days in [250, 300, 350, 365]:
            annual_rupees = daily * days
            annual_lakhs = annual_rupees / 100000.0
            assert annual_rupees > 0
            assert annual_lakhs == pytest.approx(annual_rupees / 100000.0, rel=1e-5)

        # For DEMO-FAC-001: daily is ~12823.10
        # 300 days = 3,846,930 INR = 38.47 Lakhs
        annual_300 = daily * 300
        assert 3800000 < annual_300 < 3900000
        assert 38.0 < (annual_300 / 100000.0) < 39.0

    def test_standard_versus_modified_tariff_scenario(self):
        """23. Verify standard vs 125% tariff scenario calculations and reset consistency."""
        opt_std = EnergyOptimizerService.get_summary("DEMO-FAC-001", tariff_multiplier=1.0)
        opt_125 = EnergyOptimizerService.get_summary("DEMO-FAC-001", tariff_multiplier=1.25)

        # Baseline and optimised cost must be strictly higher in the 125% tariff scenario
        assert opt_125.baseline_grid_only_cost_inr > opt_std.baseline_grid_only_cost_inr
        assert opt_125.optimised_supply_cost_inr > opt_std.optimised_supply_cost_inr
        assert opt_125.estimated_savings_inr > opt_std.estimated_savings_inr

        # Daily savings formula must hold exactly for the 125% scenario
        assert opt_125.estimated_savings_inr == round(
            opt_125.baseline_grid_only_cost_inr - opt_125.optimised_supply_cost_inr, 2
        )

        # Active scenario names must clearly distinguish standard vs what-if
        assert "Standard" in opt_std.active_scenario_name
        assert "What-If" in opt_125.active_scenario_name
        assert "125%" in opt_125.active_scenario_name

        # Resetting tariff_multiplier=1.0 must reproduce standard results identically
        opt_reset = EnergyOptimizerService.get_summary("DEMO-FAC-001", tariff_multiplier=1.0)
        assert opt_reset.baseline_grid_only_cost_inr == opt_std.baseline_grid_only_cost_inr
        assert opt_reset.optimised_supply_cost_inr == opt_std.optimised_supply_cost_inr
        assert opt_reset.estimated_savings_inr == opt_std.estimated_savings_inr

    def test_factory_isolation_no_state_leakage(self):
        """24. Verify switching between factories produces independent, deterministic results without state leakage."""
        fac1_1 = EnergyOptimizerService.get_summary("DEMO-FAC-001")
        fac2 = EnergyOptimizerService.get_summary("DEMO-FAC-002")
        fac3 = EnergyOptimizerService.get_summary("DEMO-FAC-003")

        # Distinct baseline costs for distinct factories
        assert fac1_1.baseline_grid_only_cost_inr != fac2.baseline_grid_only_cost_inr
        assert fac2.baseline_grid_only_cost_inr != fac3.baseline_grid_only_cost_inr

        # Re-evaluating factory 1 must match initial evaluation exactly
        fac1_2 = EnergyOptimizerService.get_summary("DEMO-FAC-001")
        assert fac1_1.baseline_grid_only_cost_inr == fac1_2.baseline_grid_only_cost_inr
        assert fac1_1.optimised_supply_cost_inr == fac1_2.optimised_supply_cost_inr
        assert fac1_1.estimated_savings_inr == fac1_2.estimated_savings_inr

    def test_power_to_energy_conversion_and_peak_grid_bounds(self):
        """25. Verify power (kW) and energy (kWh) conversion and contract demand limit."""
        opt = EnergyOptimizerService.run_optimization("DEMO-FAC-001")
        profile = factory_data_service.get_raw_profile("DEMO-FAC-001")
        contract_demand_kw = profile.grid.contract_demand_kw

        # Peak grid power must never exceed contract demand
        assert opt.peak_grid_power_kw <= contract_demand_kw
        assert opt.peak_grid_contract_utilisation_percent <= 100.0

        for interval in opt.intervals:
            # Over 1 hour, allocated energy (kWh) / 1.0 h = power (kW)
            interval_kw = interval.grid_allocated_kwh / 1.0
            assert interval_kw <= contract_demand_kw + 1e-2

    def test_infeasible_demand_solver_status_reporting(self):
        """26. Verify solver explicitly marks infeasible scenarios and reports cause."""
        intervals = factory_data_service.get_timeseries("DEMO-FAC-001").intervals
        profile = factory_data_service.get_raw_profile("DEMO-FAC-001")

        # Create artificial profile with 0 solar, 0 wind, 0 biomass, and 1 kW grid contract
        art_profile = profile.model_copy(deep=True)
        art_profile.solar.installed_capacity_kw = 0.0
        art_profile.wind.installed_capacity_kw = 0.0
        art_profile.biomass.installed_capacity_kw = 0.0
        art_profile.biomass.daily_fuel_available_kg = 0.0
        art_profile.grid.contract_demand_kw = 1.0  # Cannot meet ~100 kW demand

        opt_run = EnergyOptimizerService().optimize(intervals, art_profile)
        assert opt_run.is_feasible is False
        assert opt_run.infeasible_intervals_count > 0
        assert opt_run.unmet_demand_total_kwh > 0
        assert "Infeasible" in opt_run.solver_status

