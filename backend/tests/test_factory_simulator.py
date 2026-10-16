"""Automated test suite for the Phase 2 Synthetic Factory Data Engine.

Tests deterministic generation, physical constraints, anomaly injection,
data integrity, and API endpoint contracts.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.data.factory_config import get_default_factory_profile
from app.data.factory_simulator import FactorySimulator
from app.services.factory_data_service import factory_data_service

client = TestClient(app)


class TestFactorySimulator:
    """Unit tests for the FactorySimulator simulation engine."""

    def test_repeatability_with_same_seed(self):
        """Verify that identical seeds produce identical 24-hour datasets."""
        profile = get_default_factory_profile()
        sim1 = FactorySimulator(profile=profile, seed=42, simulation_date="2026-10-14")
        sim2 = FactorySimulator(profile=profile, seed=42, simulation_date="2026-10-14")

        data1 = sim1.generate_timeseries()
        data2 = sim2.generate_timeseries()

        assert len(data1) == len(data2) == 24
        for i in range(24):
            assert data1[i].total_factory_demand_kw == data2[i].total_factory_demand_kw
            assert data1[i].total_factory_energy_demand_kwh == data2[i].total_factory_energy_demand_kwh
            assert data1[i].generation.solar_power_kw == data2[i].generation.solar_power_kw
            assert data1[i].generation.wind_power_kw == data2[i].generation.wind_power_kw
            assert data1[i].generation.biomass_max_power_kw == data2[i].generation.biomass_max_power_kw
            assert data1[i].actual_production_output_units == data2[i].actual_production_output_units

    def test_different_seeds_produce_different_data(self):
        """Verify that varying seeds introduces stochastic variance."""
        profile = get_default_factory_profile()
        sim1 = FactorySimulator(profile=profile, seed=42)
        sim2 = FactorySimulator(profile=profile, seed=999)

        data1 = sim1.generate_timeseries()
        data2 = sim2.generate_timeseries()

        # Due to stochastic variations in wind/active machine powers, totals should differ
        total1 = sum(i.total_factory_energy_demand_kwh for i in data1)
        total2 = sum(i.total_factory_energy_demand_kwh for i in data2)
        assert total1 != total2

    def test_exactly_24_intervals(self):
        """Verify that exactly 24 intervals are generated."""
        sim = FactorySimulator(seed=42)
        intervals = sim.generate_timeseries()
        assert len(intervals) == 24
        for idx, item in enumerate(intervals):
            assert item.interval_index == idx
            assert item.interval_duration_hours == 1.0

    def test_timestamp_ordering_and_uniqueness(self):
        """Verify timestamps are strictly sequential and unique ISO 8601 strings."""
        sim = FactorySimulator(seed=42)
        intervals = sim.generate_timeseries()
        timestamps = [item.timestamp for item in intervals]

        assert len(set(timestamps)) == 24
        parsed = [datetime.fromisoformat(ts) for ts in timestamps]
        for i in range(len(parsed) - 1):
            assert parsed[i] < parsed[i + 1]
            # Ensure consecutive 1-hour gaps
            diff_seconds = (parsed[i + 1] - parsed[i]).total_seconds()
            assert diff_seconds == 3600

    def test_non_negative_values(self):
        """Ensure all power, energy, production, and tariff values are non-negative."""
        sim = FactorySimulator(seed=42)
        intervals = sim.generate_timeseries()

        for item in intervals:
            assert item.total_factory_demand_kw >= 0.0
            assert item.total_factory_energy_demand_kwh >= 0.0
            assert item.actual_production_output_units >= 0.0
            assert item.production_demand_units >= 0.0
            assert item.facility_baseload_kwh >= 0.0

            assert item.generation.solar_power_kw >= 0.0
            assert item.generation.solar_energy_kwh >= 0.0
            assert item.generation.wind_power_kw >= 0.0
            assert item.generation.wind_energy_kwh >= 0.0
            assert item.generation.biomass_max_power_kw >= 0.0
            assert item.generation.biomass_max_energy_kwh >= 0.0
            assert item.generation.total_renewable_available_kwh >= 0.0

            assert item.grid.tariff_rate_inr_per_kwh > 0.0
            assert item.grid.supply_capacity_kw > 0.0

            for zone in item.zones:
                assert zone.power_kw >= 0.0
                assert zone.energy_kwh >= 0.0
                assert zone.production_units >= 0.0
                for machine in zone.machines:
                    assert machine.power_kw >= 0.0
                    assert machine.energy_kwh >= 0.0

    def test_solar_daylight_profile(self):
        """Verify solar generation adheres to sunrise/sunset constraints and peaks midday."""
        sim = FactorySimulator(seed=42)
        intervals = sim.generate_timeseries()

        # Night hours (00:00 to 05:00 and 19:00 to 23:00) must be 0 kW
        for hour in [0, 1, 2, 3, 4, 5, 19, 20, 21, 22, 23]:
            assert intervals[hour].generation.solar_power_kw == 0.0
            assert intervals[hour].generation.solar_energy_kwh == 0.0

        # Daylight hours (07:00 to 17:00) must be strictly positive
        for hour in range(7, 18):
            assert intervals[hour].generation.solar_power_kw > 0.0

        # Midday peak (Hour 12 or 13) should be highest
        midday_solar = intervals[12].generation.solar_power_kw
        morning_solar = intervals[8].generation.solar_power_kw
        late_solar = intervals[16].generation.solar_power_kw
        assert midday_solar > morning_solar
        assert midday_solar > late_solar

    def test_renewable_generation_capacity_constraints(self):
        """Verify generation never exceeds installed nameplate ratings."""
        profile = get_default_factory_profile()
        sim = FactorySimulator(profile=profile, seed=42)
        intervals = sim.generate_timeseries()

        for item in intervals:
            assert item.generation.solar_power_kw <= profile.solar.installed_capacity_kw
            assert item.generation.wind_power_kw <= profile.wind.installed_capacity_kw
            assert item.generation.biomass_max_power_kw <= profile.biomass.installed_capacity_kw

    def test_biomass_availability_and_fuel_limits(self):
        """Verify biomass availability respects max capacity and daily fuel energy constraints."""
        profile = get_default_factory_profile()
        sim = FactorySimulator(profile=profile, seed=42)
        intervals = sim.generate_timeseries()

        for item in intervals:
            assert item.generation.biomass_max_power_kw <= profile.biomass.installed_capacity_kw

        # Total available biomass generation across 24h cannot exceed fuel capacity
        total_biomass = sum(i.generation.biomass_max_energy_kwh for i in intervals)
        assert total_biomass <= profile.biomass.daily_energy_capacity_kwh + 1.0

    def test_injected_anomalies_exist_and_reproducible(self):
        """Verify all 3 injected anomaly scenarios are present and correctly flagged."""
        sim = FactorySimulator(seed=42)
        anomalies = sim.get_anomaly_scenarios()
        assert len(anomalies) == 3

        scenario_ids = {a.scenario_id for a in anomalies}
        assert "ANOMALY_IDLE_WASTE_001" in scenario_ids
        assert "ANOMALY_CONSUMPTION_SPIKE_002" in scenario_ids
        assert "ANOMALY_PEAK_THRESHOLD_003" in scenario_ids

        intervals = sim.generate_timeseries()
        # Hour 3 has ANOMALY_IDLE_WASTE_001
        assert "ANOMALY_IDLE_WASTE_001" in intervals[3].metadata.active_anomaly_ids
        # Hour 11 has ANOMALY_CONSUMPTION_SPIKE_002
        assert "ANOMALY_CONSUMPTION_SPIKE_002" in intervals[11].metadata.active_anomaly_ids
        # Hour 19 has ANOMALY_PEAK_THRESHOLD_003
        assert "ANOMALY_PEAK_THRESHOLD_003" in intervals[19].metadata.active_anomaly_ids
        assert intervals[19].total_factory_demand_kw == 238.5

    def test_overview_consistency_with_timeseries(self):
        """Verify overview summary metrics exactly match aggregated timeseries values."""
        sim = FactorySimulator(seed=42)
        intervals = sim.generate_timeseries()
        overview = sim.generate_overview(intervals)

        assert overview.total_intervals == 24
        assert overview.total_factory_energy_demand_kwh == round(
            sum(i.total_factory_energy_demand_kwh for i in intervals), 2
        )
        assert overview.total_production_units == round(
            sum(i.actual_production_output_units for i in intervals), 1
        )
        assert overview.renewable_energy_availability.solar_total_kwh == round(
            sum(i.generation.solar_energy_kwh for i in intervals), 2
        )
        assert overview.renewable_energy_availability.wind_total_kwh == round(
            sum(i.generation.wind_energy_kwh for i in intervals), 2
        )
        assert overview.highest_demand_interval.demand_kw == max(
            i.total_factory_demand_kw for i in intervals
        )
        assert overview.total_anomalies_count == 3


class TestFactoryApiEndpoints:
    """Integration tests for FastAPI endpoints."""

    def test_get_factory_profile(self):
        """GET /api/factory/profile returns HTTP 200 with complete profile."""
        response = client.get("/api/factory/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["factory_id"] == "DEMO-FAC-001"
        assert "PrecisionWorks" in data["name"]
        assert data["currency"] == "INR"
        assert len(data["zones"]) == 3
        assert len(data["shifts"]) == 3
        assert data["solar"]["installed_capacity_kw"] == 100.0
        assert data["wind"]["installed_capacity_kw"] == 60.0
        assert data["biomass"]["installed_capacity_kw"] == 50.0
        assert data["grid"]["contract_demand_kw"] == 250.0
        assert data["simulation_metadata"]["is_synthetic"] is True

    def test_get_factory_timeseries(self):
        """GET /api/factory/timeseries returns HTTP 200 with 24 ordered intervals."""
        response = client.get("/api/factory/timeseries")
        assert response.status_code == 200
        data = response.json()
        assert data["total_intervals"] == 24
        assert len(data["intervals"]) == 24
        # Verify first and last interval
        assert data["intervals"][0]["interval_index"] == 0
        assert data["intervals"][23]["interval_index"] == 23
        assert data["simulation_metadata"]["is_synthetic"] is True

    def test_get_anomaly_scenarios(self):
        """GET /api/factory/anomaly-scenarios returns 3 scenarios with diagnostic reasons."""
        response = client.get("/api/factory/anomaly-scenarios")
        assert response.status_code == 200
        data = response.json()
        assert data["total_anomalies"] == 3
        scenarios = data["scenarios"]
        assert len(scenarios) == 3
        for s in scenarios:
            assert "scenario_id" in s
            assert "category" in s
            assert "expected_baseline_value" in s
            assert "observed_simulated_value" in s
            assert "reason" in s
            assert s["severity"] in ["low", "medium", "high", "critical"]

    def test_get_factory_overview(self):
        """GET /api/factory/overview returns consistent high-level metrics."""
        response = client.get("/api/factory/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["total_intervals"] == 24
        assert data["total_factory_energy_demand_kwh"] > 0
        assert data["total_production_units"] > 0
        assert data["renewable_energy_availability"]["total_renewable_available_kwh"] > 0
        assert data["highest_demand_interval"]["demand_kw"] == 238.5  # Hour 19 peak anomaly
        assert data["total_anomalies_count"] == 3

    def test_phase1_health_and_root_endpoints_preserved(self):
        """Ensure Phase 1 endpoints continue functioning without regression."""
        res_health = client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "ok"

        res_root = client.get("/")
        assert res_root.status_code == 200
        assert res_root.json()["name"] == "GridMind AI"
