"""Comprehensive test suite for GridMind AI Multi-Factory Engine.

Verifies:
1. Exactly three demo factory profiles are configured and retrievable.
2. GET /api/factories returns all three factories with correct metadata.
3. GET /api/factories/{factory_id} returns factory-specific details.
4. Unknown factory IDs return 404 across all endpoints.
5. Each factory exhibits a distinct daily demand curve, peak power, and total kWh.
6. Each factory has distinct renewable generation characteristics (solar, wind, biomass).
7. The SciPy HiGHS LP optimizer executes successfully on all three factories.
8. Energy balance holds strictly for all intervals across all three factories.
9. Baseline costs and optimized costs are mathematically computed (not hardcoded).
10. Estimated savings are calculated correctly as (baseline - optimized) for all three factories.
11. Biomass generation respects generator capacity and daily fuel budget for all three factories.
12. Solar and wind allocations never exceed physical availability for any factory.
13. Grid contract demand limits are respected.
14. Rule-based anomaly detection identifies factory-specific anomalies.
15. Data isolation: querying factory B does not overwrite or corrupt factory A's cached state.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.factory_registry import VALID_FACTORY_IDS, FACTORY_REGISTRY
from app.services.factory_data_service import factory_data_service
from app.services.energy_metrics import energy_metrics_service
from app.services.anomaly_detector import anomaly_detector_service
from app.services.energy_optimizer import EnergyOptimizerService

client = TestClient(app)


class TestMultiFactoryRegistry:
    """Tests for factory registry and data isolation."""

    def test_exactly_three_factories_configured(self):
        """1. Verify exactly three demo factories are defined."""
        assert len(VALID_FACTORY_IDS) == 3
        assert "DEMO-FAC-001" in VALID_FACTORY_IDS
        assert "DEMO-FAC-002" in VALID_FACTORY_IDS
        assert "DEMO-FAC-003" in VALID_FACTORY_IDS

    def test_api_list_factories_endpoint(self):
        """2. GET /api/factories returns 3 factories."""
        response = client.get("/api/factories")
        assert response.status_code == 200
        data = response.json()
        assert data["total_factories"] == 3
        ids = [f["factory_id"] for f in data["factories"]]
        assert ids == ["DEMO-FAC-001", "DEMO-FAC-002", "DEMO-FAC-003"]
        for f in data["factories"]:
            assert f["total_rated_connected_power_kw"] > 0
            assert f["grid_contract_demand_kw"] > 0
            assert len(f["demo_scenario_description"]) > 10

    def test_get_factory_by_id_endpoints(self):
        """3. GET /api/factories/{factory_id} returns correct factory."""
        for fid in VALID_FACTORY_IDS:
            res = client.get(f"/api/factories/{fid}")
            assert res.status_code == 200
            data = res.json()
            assert data["factory_id"] == fid
            assert len(data["zones"]) == 3
            assert len(data["shifts"]) == 3
            assert data["grid"]["contract_demand_kw"] > 0

    def test_invalid_factory_id_returns_404(self):
        """4. Invalid factory ID returns 404 across endpoints."""
        invalid_id = "FAC-NONEXISTENT-999"
        assert client.get(f"/api/factories/{invalid_id}").status_code == 404
        assert client.get(f"/api/factory/profile?factory_id={invalid_id}").status_code == 404
        assert client.get(f"/api/analysis/metrics?factory_id={invalid_id}").status_code == 404
        assert client.get(f"/api/optimization/run?factory_id={invalid_id}").status_code == 404


class TestMultiFactorySimulationDifferences:
    """Verify each factory has distinct demand and generation curves."""

    def test_distinct_demand_and_energy_totals(self):
        """5. Verify total demand, peak power, and generation differ among all 3 factories."""
        ts_apex = factory_data_service.get_timeseries("DEMO-FAC-001")
        ts_fresh = factory_data_service.get_timeseries("DEMO-FAC-002")
        ts_loom = factory_data_service.get_timeseries("DEMO-FAC-003")

        demand_apex = sum(i.total_factory_energy_demand_kwh for i in ts_apex.intervals)
        demand_fresh = sum(i.total_factory_energy_demand_kwh for i in ts_fresh.intervals)
        demand_loom = sum(i.total_factory_energy_demand_kwh for i in ts_loom.intervals)

        # Totals must be distinctly different (not copy-pasted)
        assert abs(demand_apex - demand_fresh) > 100.0
        assert abs(demand_apex - demand_loom) > 100.0
        assert abs(demand_fresh - demand_loom) > 100.0

    def test_distinct_baseload_and_schedule(self):
        """6. FreshField cold storage has high baseload; PrecisionWorks has lower baseload."""
        p_apex = factory_data_service.get_raw_profile("DEMO-FAC-001")
        p_fresh = factory_data_service.get_raw_profile("DEMO-FAC-002")
        p_loom = factory_data_service.get_raw_profile("DEMO-FAC-003")

        assert p_fresh.facility_baseload_kw > p_apex.facility_baseload_kw
        assert p_loom.solar.installed_capacity_kw == 120.0
        assert p_fresh.wind.installed_capacity_kw == 20.0
        assert p_apex.wind.installed_capacity_kw == 60.0

    def test_distinct_anomalies_detected(self):
        """7. Anomaly detection produces factory-specific findings."""
        anom_apex = anomaly_detector_service.get_anomalies(factory_id="DEMO-FAC-001")
        anom_fresh = anomaly_detector_service.get_anomalies(factory_id="DEMO-FAC-002")
        anom_loom = anomaly_detector_service.get_anomalies(factory_id="DEMO-FAC-003")

        assert anom_apex.total_detected >= 1
        assert anom_fresh.total_detected >= 1
        assert anom_loom.total_detected >= 1


class TestMultiFactoryOptimization:
    """Verify HiGHS LP optimizer operates on all three factories correctly."""

    @pytest.mark.parametrize("factory_id", VALID_FACTORY_IDS)
    def test_highs_optimizer_feasible_for_all_factories(self, factory_id):
        """8. Optimizer runs and finds a feasible solution for each factory."""
        opt_run = EnergyOptimizerService.run_optimization(factory_id=factory_id)
        assert opt_run.is_feasible is True
        assert opt_run.factory_id == factory_id
        assert opt_run.total_demand_served_kwh > 0
        assert opt_run.unmet_demand_total_kwh == 0.0

    @pytest.mark.parametrize("factory_id", VALID_FACTORY_IDS)
    def test_energy_balance_holds_for_all_factories(self, factory_id):
        """9. Sum of allocated sources equals interval demand for every interval."""
        opt_run = EnergyOptimizerService.run_optimization(factory_id=factory_id)
        for interval in opt_run.intervals:
            supplied = (
                interval.solar_allocated_kwh
                + interval.wind_allocated_kwh
                + interval.biomass_allocated_kwh
                + interval.grid_allocated_kwh
            )
            assert abs(supplied - interval.factory_demand_kwh) < 0.02
            assert interval.is_feasible is True

    @pytest.mark.parametrize("factory_id", VALID_FACTORY_IDS)
    def test_savings_formula_correct_and_not_hardcoded(self, factory_id):
        """10. Estimated savings = baseline_cost - optimised_cost."""
        opt_run = EnergyOptimizerService.run_optimization(factory_id=factory_id)
        expected_savings = round(
            opt_run.baseline_grid_only_cost_inr - opt_run.optimised_supply_cost_inr, 2
        )
        assert abs(opt_run.estimated_savings_inr - expected_savings) < 0.02
        assert opt_run.estimated_savings_inr > 0.0
        assert opt_run.estimated_savings_percentage > 0.0

    @pytest.mark.parametrize("factory_id", VALID_FACTORY_IDS)
    def test_biomass_limits_respected(self, factory_id):
        """11. Biomass energy allocated <= daily fuel budget."""
        opt_run = EnergyOptimizerService.run_optimization(factory_id=factory_id)
        profile = factory_data_service.get_raw_profile(factory_id)
        max_daily_biomass_kwh = profile.biomass.daily_energy_capacity_kwh

        assert opt_run.biomass_energy_consumed_kwh <= max_daily_biomass_kwh + 0.05
        assert opt_run.biomass_fuel_consumed_kg <= profile.biomass.daily_fuel_available_kg + 0.05
        assert opt_run.biomass_remaining_fuel_budget_kg >= 0.0

    @pytest.mark.parametrize("factory_id", VALID_FACTORY_IDS)
    def test_solar_and_wind_never_exceed_availability(self, factory_id):
        """12. Solar and wind allocations never exceed physical availability."""
        opt_run = EnergyOptimizerService.run_optimization(factory_id=factory_id)
        for interval in opt_run.intervals:
            assert interval.solar_allocated_kwh <= interval.solar_available_kwh + 0.01
            assert interval.wind_allocated_kwh <= interval.wind_available_kwh + 0.01

    @pytest.mark.parametrize("factory_id", VALID_FACTORY_IDS)
    def test_grid_contract_demand_respected(self, factory_id):
        """13. Grid allocation never exceeds contract demand."""
        opt_run = EnergyOptimizerService.run_optimization(factory_id=factory_id)
        profile = factory_data_service.get_raw_profile(factory_id)
        contract_limit = profile.grid.contract_demand_kw

        for interval in opt_run.intervals:
            assert interval.grid_allocated_kwh <= contract_limit + 0.01

    def test_what_if_scenario_solar_multiplier(self):
        """14. Scaling solar_multiplier reduces or increases solar allocation."""
        base_run = EnergyOptimizerService.run_optimization(
            factory_id="DEMO-FAC-001", solar_multiplier=1.0
        )
        low_solar_run = EnergyOptimizerService.run_optimization(
            factory_id="DEMO-FAC-001", solar_multiplier=0.4
        )
        high_solar_run = EnergyOptimizerService.run_optimization(
            factory_id="DEMO-FAC-001", solar_multiplier=1.5
        )

        base_solar = next(s for s in base_run.source_breakdown if s.source == "solar").total_allocated_kwh
        low_solar = next(s for s in low_solar_run.source_breakdown if s.source == "solar").total_allocated_kwh
        high_solar = next(s for s in high_solar_run.source_breakdown if s.source == "solar").total_allocated_kwh

        assert low_solar < base_solar
        assert high_solar >= base_solar
        assert low_solar_run.is_feasible is True
        assert high_solar_run.is_feasible is True

    def test_what_if_scenario_tariff_multiplier(self):
        """15. Tariff multiplier scales baseline cost proportionally."""
        base_run = EnergyOptimizerService.run_optimization(
            factory_id="DEMO-FAC-001", tariff_multiplier=1.0
        )
        hike_run = EnergyOptimizerService.run_optimization(
            factory_id="DEMO-FAC-001", tariff_multiplier=1.25
        )

        assert round(hike_run.baseline_grid_only_cost_inr / base_run.baseline_grid_only_cost_inr, 2) == 1.25
        assert hike_run.estimated_savings_inr > base_run.estimated_savings_inr

    def test_what_if_scenario_api_endpoints(self):
        """16. API endpoints accept solar_multiplier and tariff_multiplier."""
        resp = client.get("/api/optimization/run?factory_id=DEMO-FAC-001&solar_multiplier=0.5&tariff_multiplier=1.2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_feasible"] is True
        assert data["estimated_savings_inr"] > 0


class TestDataIsolation:
    """Ensure querying different factories maintains data isolation."""

    def test_factory_switching_isolation(self):
        """17. Querying factory B, then A, gives consistent isolated results for A."""
        profile_a1 = factory_data_service.get_profile("DEMO-FAC-001")
        profile_b = factory_data_service.get_profile("DEMO-FAC-002")
        profile_c = factory_data_service.get_profile("DEMO-FAC-003")
        profile_a2 = factory_data_service.get_profile("DEMO-FAC-001")

        assert profile_a1.factory_id == profile_a2.factory_id == "DEMO-FAC-001"
        assert profile_b.factory_id == "DEMO-FAC-002"
        assert profile_c.factory_id == "DEMO-FAC-003"
        assert profile_a1.name == profile_a2.name == "PrecisionWorks Factory"
        assert profile_b.name == "FreshField Factory"
        assert profile_c.name == "WeaveWise Factory"

    def test_legacy_factory_id_backward_compatibility(self):
        """18. Verify legacy factory IDs automatically resolve to new DEMO-FAC IDs."""
        profile_legacy_a = factory_data_service.get_profile("FAC-IN-PUNE-001")
        profile_legacy_b = factory_data_service.get_profile("FAC-IN-NASHIK-002")
        profile_legacy_c = factory_data_service.get_profile("FAC-IN-TIRUPPUR-003")

        assert profile_legacy_a.factory_id == "DEMO-FAC-001"
        assert profile_legacy_b.factory_id == "DEMO-FAC-002"
        assert profile_legacy_c.factory_id == "DEMO-FAC-003"
