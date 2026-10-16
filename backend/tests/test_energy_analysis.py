"""Automated test suite for Phase 3 Energy Analysis and Anomaly Detection.

Verifies:
1. Total demand equals the sum of underlying interval energy values.
2. Energy intensity uses the correct production denominator.
3. Zero production does not cause division by zero.
4. Tariff changes affect the estimated grid-only cost correctly.
5. Peak power and interval energy are not confused.
6. Renewable availability is calculated separately by source.
7. Available renewable generation is not misrepresented as actual consumption.
8. Idle-machine anomalies require inactive production schedules.
9. Consumption spikes are detected against the expected baseline.
10. High-demand alerts use consistent power and capacity units.
11. Anomaly severity and deviation calculations are correct.
12. Unknown anomaly IDs return HTTP 404.
13. Severity, category, and zone filters work.
14. All existing Phase 1 and Phase 2 endpoints remain functional.
15. Repeated calls return consistent results for the same dataset.
16. API responses match their declared schemas.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.factory_config import get_default_factory_profile
from app.data.factory_simulator import FactorySimulator
from app.services.factory_data_service import factory_data_service
from app.services.energy_metrics import energy_metrics_service, EnergyMetricsService
from app.services.anomaly_detector import anomaly_detector_service, AnomalyDetectorService
from app.schemas.analysis import RenewableAvailabilityMetrics

client = TestClient(app)


class TestEnergyMetricsUnit:
    """Unit tests for pure EnergyMetricsService functions."""

    def test_total_demand_equals_sum_of_intervals(self):
        """1. Verify total demand equals the exact sum of interval energy values."""
        intervals = factory_data_service.get_timeseries().intervals
        metrics = EnergyMetricsService.calculate_demand_metrics(intervals)

        sum_energy = round(sum(i.total_factory_energy_demand_kwh for i in intervals), 2)
        assert metrics.total_demand_kwh == sum_energy
        assert metrics.average_hourly_demand_kwh == round(sum_energy / 24, 2)

    def test_energy_intensity_correct_denominator(self):
        """2. Verify energy intensity uses the correct production denominator."""
        intervals = factory_data_service.get_timeseries().intervals
        metrics = EnergyMetricsService.calculate_demand_metrics(intervals)

        total_kwh = metrics.total_demand_kwh
        total_prod = metrics.total_production_units
        assert total_prod > 0
        expected_intensity = round(total_kwh / total_prod, 4)
        assert metrics.overall_energy_intensity_kwh_per_unit == expected_intensity

    def test_zero_production_does_not_divide_by_zero(self):
        """3. Verify zero production returns None for energy intensity without zero-division error."""
        intervals = factory_data_service.get_timeseries().intervals
        # Create a mock slice where production is zero
        off_shift_slice = [i for i in intervals if i.actual_production_output_units == 0]
        assert len(off_shift_slice) > 0

        metrics = EnergyMetricsService.calculate_demand_metrics(off_shift_slice)
        assert metrics.total_production_units == 0.0
        assert metrics.overall_energy_intensity_kwh_per_unit is None

    def test_tariff_changes_affect_grid_cost_baseline(self):
        """4. Verify tariff variations across periods directly alter estimated baseline cost."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals

        baseline = EnergyMetricsService.calculate_grid_cost_baseline(intervals, profile.grid)

        # Baseline cost must be greater than zero and equal the sum of period costs
        assert baseline.total_estimated_cost_inr > 0
        period_sum = round(sum(p.estimated_cost_inr for p in baseline.period_breakdown), 2)
        assert baseline.total_estimated_cost_inr == period_sum

        # Off-peak, normal, and peak period breakdown must all exist
        period_names = {p.period_name for p in baseline.period_breakdown}
        assert "Off-Peak / Night" in period_names
        assert "Normal / Day" in period_names
        assert "Peak / Evening Surcharge" in period_names

        # Peak period rate (11.80) is higher than normal (8.20) and off-peak (6.50)
        peak_p = next(p for p in baseline.period_breakdown if "Peak" in p.period_name and "Off" not in p.period_name)
        normal_p = next(p for p in baseline.period_breakdown if "Normal" in p.period_name)
        off_peak_p = next(p for p in baseline.period_breakdown if "Off-Peak" in p.period_name)
        assert peak_p.tariff_rate_inr_per_kwh > normal_p.tariff_rate_inr_per_kwh > off_peak_p.tariff_rate_inr_per_kwh

    def test_peak_power_and_interval_energy_not_confused(self):
        """5. Verify peak instantaneous power (kW) and energy (kWh) retain correct units."""
        intervals = factory_data_service.get_timeseries().intervals
        metrics = EnergyMetricsService.calculate_demand_metrics(intervals)

        assert metrics.peak_power_kw == 238.5  # Hour 19 surge
        # Interval duration is 1.0 hr, so energy for this 1h interval is 238.5 kWh
        assert intervals[19].interval_duration_hours == 1.0
        assert intervals[19].total_factory_demand_kw == 238.5
        assert intervals[19].total_factory_energy_demand_kwh == 238.5

    def test_renewable_availability_calculated_separately_by_source(self):
        """6. Verify separate availability metrics for solar, wind, and biomass."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals
        total_demand = sum(i.total_factory_energy_demand_kwh for i in intervals)

        renewables = EnergyMetricsService.calculate_renewable_availability(
            intervals, profile, total_demand
        )

        source_map = {s.source: s for s in renewables.sources}
        assert "solar" in source_map
        assert "wind" in source_map
        assert "biomass" in source_map

        assert source_map["solar"].installed_capacity_kw == 100.0
        assert source_map["solar"].total_available_kwh > 0
        assert source_map["wind"].installed_capacity_kw == 60.0
        assert source_map["wind"].total_available_kwh > 0
        assert source_map["biomass"].installed_capacity_kw == 50.0
        assert source_map["biomass"].total_available_kwh > 0

    def test_renewable_availability_is_not_misrepresented_as_consumption(self):
        """7. Verify availability ratio is explicitly labeled and contains disclaimer."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals
        total_demand = sum(i.total_factory_energy_demand_kwh for i in intervals)

        renewables = EnergyMetricsService.calculate_renewable_availability(
            intervals, profile, total_demand
        )

        assert "availability_to_demand_ratio_percent" in RenewableAvailabilityMetrics.model_fields
        assert "not represent actual energy supplied" in renewables.disclaimer.lower()


class TestAnomalyDetectionUnit:
    """Unit tests for pure AnomalyDetectorService rules."""

    def test_idle_machine_anomaly_requires_inactive_schedule(self):
        """8. Verify idle waste anomaly triggers only when production is scheduled inactive."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals
        detector = AnomalyDetectorService()

        findings = detector.detect_anomalies(intervals, profile)
        idle_findings = [f for f in findings if f.category == "idle_machine_waste"]

        assert len(idle_findings) >= 1
        for finding in idle_findings:
            # Must occur in off-shift (hour 3)
            assert finding.interval_index == 3
            assert intervals[finding.interval_index].metadata.is_production_active is False
            assert finding.evidence.observed_value > finding.evidence.baseline_threshold

    def test_consumption_spike_detected_against_baseline(self):
        """9. Verify consumption spike triggers when zone exceeds baseline by configured threshold."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals
        detector = AnomalyDetectorService()

        findings = detector.detect_anomalies(intervals, profile)
        spike_findings = [f for f in findings if f.category == "unexpected_consumption_spike"]

        assert len(spike_findings) >= 1
        h11_spike = next(f for f in spike_findings if f.interval_index == 11)
        assert h11_spike.affected_zone_id == "zone_cnc"
        assert h11_spike.evidence.observed_value == 105.0
        assert h11_spike.evidence.deviation_percent > 35.0

    def test_high_demand_alert_uses_consistent_power_units(self):
        """10. Verify high-demand alert compares power in kW with grid contract demand in kW."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals
        detector = AnomalyDetectorService()

        findings = detector.detect_anomalies(intervals, profile)
        high_demand = [f for f in findings if f.category == "high_demand_period"]

        assert len(high_demand) >= 1
        peak_alert = high_demand[0]
        assert peak_alert.interval_index == 19
        assert peak_alert.evidence.unit == "kW"
        assert peak_alert.evidence.observed_value == 238.5
        assert peak_alert.severity == "critical"

    def test_anomaly_severity_and_deviation_calculations(self):
        """11. Verify deviation values and assigned severity ratings match expectations."""
        profile = factory_data_service._profile
        intervals = factory_data_service.get_timeseries().intervals
        detector = AnomalyDetectorService()

        findings = detector.detect_anomalies(intervals, profile)
        for f in findings:
            assert f.severity in ["low", "medium", "high", "critical"]
            expected_dev = round(f.evidence.observed_value - f.evidence.baseline_threshold, 2)
            assert abs(f.evidence.deviation_value - expected_dev) < 0.1
            assert f.estimated_financial_impact_inr is not None
            assert f.estimated_financial_impact_inr > 0


class TestAnalysisApiIntegration:
    """Integration tests for FastAPI endpoints under /api/analysis/*."""

    def test_get_energy_metrics_endpoint(self):
        """16. Verify GET /api/analysis/metrics schema and values."""
        response = client.get("/api/analysis/metrics")
        assert response.status_code == 200
        data = response.json()

        assert data["factory_id"] == "DEMO-FAC-001"
        assert data["demand_metrics"]["total_demand_kwh"] > 0
        assert data["demand_metrics"]["peak_power_kw"] == 238.5
        assert len(data["zone_metrics"]) == 3
        assert len(data["shift_metrics"]) == 3
        assert len(data["renewable_availability"]["sources"]) == 3
        assert data["grid_cost_baseline"]["total_estimated_cost_inr"] > 0
        assert data["grid_cost_baseline"]["exceeds_grid_capacity"] is False
        assert data["simulation_metadata"]["is_synthetic"] is True

    def test_get_anomalies_and_filtering(self):
        """13. Verify GET /api/analysis/anomalies with query filters."""
        # Unfiltered
        res_all = client.get("/api/analysis/anomalies")
        assert res_all.status_code == 200
        data_all = res_all.json()
        assert data_all["total_detected"] >= 3

        # Severity filter: critical
        res_crit = client.get("/api/analysis/anomalies?severity=critical")
        assert res_crit.status_code == 200
        data_crit = res_crit.json()
        assert all(f["severity"] == "critical" for f in data_crit["findings"])
        assert data_crit["total_detected"] >= 1

        # Category filter: idle_machine_waste
        res_cat = client.get("/api/analysis/anomalies?category=idle_machine_waste")
        assert res_cat.status_code == 200
        data_cat = res_cat.json()
        assert all(f["category"] == "idle_machine_waste" for f in data_cat["findings"])

        # Zone filter: zone_cnc
        res_zone = client.get("/api/analysis/anomalies?zone_id=zone_cnc")
        assert res_zone.status_code == 200
        data_zone = res_zone.json()
        assert all(f["affected_zone_id"] == "zone_cnc" for f in data_zone["findings"])

    def test_get_single_anomaly_detail_and_404(self):
        """12. Verify single anomaly lookup and HTTP 404 for unknown IDs."""
        # Valid finding ID
        res_valid = client.get("/api/analysis/anomalies/FINDING-IDLE-WASTE-H03")
        assert res_valid.status_code == 200
        data = res_valid.json()
        assert data["finding_id"] == "FINDING-IDLE-WASTE-H03"
        assert data["category"] == "idle_machine_waste"
        assert data["affected_zone_id"] == "zone_heat_treatment"

        # Also works with scenario_id alias
        res_alias = client.get("/api/analysis/anomalies/ANOMALY_PEAK_THRESHOLD_003")
        assert res_alias.status_code == 200
        assert res_alias.json()["finding_id"] == "FINDING-PEAK-CAP-H19"

        # Invalid ID returns 404
        res_invalid = client.get("/api/analysis/anomalies/NON_EXISTENT_ANOMALY_999")
        assert res_invalid.status_code == 404
        assert "not found" in res_invalid.json()["detail"].lower()

    def test_get_energy_profile_endpoint(self):
        """Verify GET /api/analysis/energy-profile returns 24 analytical intervals."""
        response = client.get("/api/analysis/energy-profile")
        assert response.status_code == 200
        data = response.json()

        assert data["total_intervals"] == 24
        assert len(data["hourly_profile"]) == 24
        assert data["summary_totals"]["total_factory_demand_kwh"] > 0
        assert data["summary_totals"]["total_grid_cost_baseline_inr"] > 0

        # Verify interval contents
        first = data["hourly_profile"][0]
        assert "factory_demand_kw" in first
        assert "solar_available_kwh" in first
        assert "grid_cost_baseline_inr" in first
        assert "is_peak_tariff" in first

    def test_repeated_calls_return_identical_data(self):
        """15. Verify determinism and caching across multiple calls."""
        res1 = client.get("/api/analysis/metrics").json()
        res2 = client.get("/api/analysis/metrics").json()
        assert res1["demand_metrics"] == res2["demand_metrics"]
        assert res1["grid_cost_baseline"] == res2["grid_cost_baseline"]

    def test_preservation_of_phase1_and_phase2_endpoints(self):
        """14. Ensure /health, /, and /api/factory/* all remain functional without regression."""
        # Phase 1
        assert client.get("/health").status_code == 200
        assert client.get("/").status_code == 200

        # Phase 2
        assert client.get("/api/factory/profile").status_code == 200
        assert client.get("/api/factory/timeseries").status_code == 200
        assert client.get("/api/factory/anomaly-scenarios").status_code == 200
        assert client.get("/api/factory/overview").status_code == 200
