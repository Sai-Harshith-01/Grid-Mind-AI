"""Rule-based, explainable anomaly detection service for GridMind AI.

Uses deterministic industrial heuristics to detect:
1. Idle-machine energy waste during non-production windows.
2. Unexpected consumption spikes exceeding zone operating thresholds.
3. High-demand surges approaching or breaching sanctioned grid contract demand.

IMPORTANT:
All detected patterns are simulated findings derived from the synthetic factory model.
They represent algorithmic diagnostic hypotheses, not physical telemetry proofs.
"""

from typing import Dict, List, Optional
from app.data.factory_config import FactoryProfile
from app.schemas.analysis import (
    AnomalyEvidence,
    AnomalyListResponse,
    DetectedAnomalyFinding,
)
from app.schemas.factory import TimeSeriesInterval
from app.services.factory_data_service import factory_data_service, DEFAULT_FACTORY_ID


class AnomalyDetectorService:
    """Service detecting and explaining industrial energy anomalies."""

    def __init__(self, spike_threshold_ratio: float = 1.35, peak_warning_ratio: float = 0.88):
        # Configurable detection thresholds
        self.spike_threshold_ratio = spike_threshold_ratio
        self.peak_warning_ratio = peak_warning_ratio

    def detect_anomalies(
        self, intervals: List[TimeSeriesInterval], profile: FactoryProfile
    ) -> List[DetectedAnomalyFinding]:
        """Run explainable detection rules against 24-hour time series intervals."""
        findings: List[DetectedAnomalyFinding] = []

        contract_demand_kw = profile.grid.contract_demand_kw
        peak_warning_threshold_kw = contract_demand_kw * self.peak_warning_ratio
        peak_critical_threshold_kw = contract_demand_kw * 0.95

        for interval in intervals:
            idx = interval.interval_index
            ts = interval.timestamp
            tariff = interval.grid.tariff_rate_inr_per_kwh

            # -------------------------------------------------------------
            # RULE 1: Idle-Machine Energy Waste (RULE_IDLE_WASTE_01)
            # Checked when interval or zone is scheduled inactive
            # -------------------------------------------------------------
            for zone in interval.zones:
                if not zone.is_active:
                    # Look up zone definition in profile for rated idle threshold
                    zone_cfg = next((z for z in profile.zones if z.zone_id == zone.zone_id), None)
                    if zone_cfg:
                        expected_idle_kw = sum(m.idle_power_kw for m in zone_cfg.machines)
                        # Tolerance buffer: 20% over normal idle
                        idle_threshold_kw = expected_idle_kw * 1.20

                        if zone.power_kw > idle_threshold_kw:
                            dev_val = round(zone.power_kw - expected_idle_kw, 2)
                            dev_pct = round((dev_val / expected_idle_kw) * 100.0, 1)
                            fin_impact = round(dev_val * tariff, 2)

                            # Identify offending machine(s) in zone
                            suspect_machine = max(zone.machines, key=lambda m: m.power_kw)

                            findings.append(
                                DetectedAnomalyFinding(
                                    finding_id=f"FINDING-IDLE-WASTE-H{idx:02d}",
                                    scenario_id="ANOMALY_IDLE_WASTE_001" if idx == 3 else None,
                                    category="idle_machine_waste",
                                    title=f"Off-Shift Standby Waste in {zone.zone_name}",
                                    severity="medium",
                                    affected_zone_id=zone.zone_id,
                                    affected_zone_name=zone.zone_name,
                                    affected_machine_id=suspect_machine.machine_id,
                                    affected_machine_name=suspect_machine.name,
                                    interval_index=idx,
                                    timestamp=ts,
                                    evidence=AnomalyEvidence(
                                        interval_index=idx,
                                        timestamp=ts,
                                        metric_name="zone_idle_power_kw",
                                        observed_value=zone.power_kw,
                                        baseline_threshold=expected_idle_kw,
                                        deviation_value=dev_val,
                                        deviation_percent=dev_pct,
                                        unit="kW",
                                        grid_tariff_inr_per_kwh=tariff,
                                    ),
                                    detection_rule_id="RULE_IDLE_WASTE_01",
                                    detection_rule_description=(
                                        f"Zone observed power ({zone.power_kw} kW) exceeded idle baseline "
                                        f"({expected_idle_kw} kW) by >20% during non-production scheduled hours."
                                    ),
                                    physical_hypothesis_notes=(
                                        f"Machinery in {zone.zone_name} (primarily {suspect_machine.name}) was left "
                                        "energized in active heating or unloader state instead of powering down to standby."
                                    ),
                                    estimated_financial_impact_inr=fin_impact,
                                    suggested_action=(
                                        "Enforce automated PLC standby lockout at shift changeover."
                                    ),
                                )
                            )

            # -------------------------------------------------------------
            # RULE 2: Unexpected Consumption Spike (RULE_CONSUMPTION_SPIKE_02)
            # Checked during active production when a zone significantly breaches baseline
            # -------------------------------------------------------------
            for zone in interval.zones:
                if zone.is_active:
                    zone_cfg = next((z for z in profile.zones if z.zone_id == zone.zone_id), None)
                    if zone_cfg:
                        # Baseline power under scheduled shift multiplier
                        baseline_kw = sum(
                            m.active_power_range_kw[0]
                            + (m.active_power_range_kw[1] - m.active_power_range_kw[0]) * 0.5
                            for m in zone_cfg.machines
                        )
                        spike_threshold_kw = baseline_kw * self.spike_threshold_ratio

                        if zone.power_kw > spike_threshold_kw:
                            dev_val = round(zone.power_kw - baseline_kw, 2)
                            dev_pct = round((dev_val / baseline_kw) * 100.0, 1)
                            fin_impact = round(dev_val * tariff, 2)
                            suspect_machine = max(zone.machines, key=lambda m: m.power_kw)

                            findings.append(
                                DetectedAnomalyFinding(
                                    finding_id=f"FINDING-SPIKE-H{idx:02d}-{zone.zone_id}",
                                    scenario_id="ANOMALY_CONSUMPTION_SPIKE_002" if idx == 11 and zone.zone_id == "zone_cnc" else None,
                                    category="unexpected_consumption_spike",
                                    title=f"Unusual Consumption Surge in {zone.zone_name}",
                                    severity="high",
                                    affected_zone_id=zone.zone_id,
                                    affected_zone_name=zone.zone_name,
                                    affected_machine_id=suspect_machine.machine_id,
                                    affected_machine_name=suspect_machine.name,
                                    interval_index=idx,
                                    timestamp=ts,
                                    evidence=AnomalyEvidence(
                                        interval_index=idx,
                                        timestamp=ts,
                                        metric_name="zone_active_power_kw",
                                        observed_value=zone.power_kw,
                                        baseline_threshold=round(baseline_kw, 2),
                                        deviation_value=dev_val,
                                        deviation_percent=dev_pct,
                                        unit="kW",
                                        grid_tariff_inr_per_kwh=tariff,
                                    ),
                                    detection_rule_id="RULE_CONSUMPTION_SPIKE_02",
                                    detection_rule_description=(
                                        f"Active zone power ({zone.power_kw} kW) exceeded normal operating baseline "
                                        f"({round(baseline_kw, 2)} kW) by >{int((self.spike_threshold_ratio - 1) * 100)}%."
                                    ),
                                    physical_hypothesis_notes=(
                                        f"Severe load surge detected on {suspect_machine.name}. Potential mechanical bind, "
                                        "pneumatic leak in unloader circuit, or transducer drift."
                                    ),
                                    estimated_financial_impact_inr=fin_impact,
                                    suggested_action=(
                                        "Inspect pneumatic ring-main isolation valves and check compressor duty cycle."
                                    ),
                                )
                            )

            # -------------------------------------------------------------
            # RULE 3: High-Demand Grid Capacity Risk (RULE_PEAK_CAPACITY_RISK_03)
            # Checked against factory-wide instantaneous demand in kW
            # -------------------------------------------------------------
            if interval.total_factory_demand_kw >= peak_warning_threshold_kw:
                dev_val = round(interval.total_factory_demand_kw - 145.0, 2)  # 145 kW normal active factory baseline
                dev_pct = round((dev_val / 145.0) * 100.0, 1)
                fin_impact = round(dev_val * tariff, 2)
                severity = (
                    "critical"
                    if interval.total_factory_demand_kw >= peak_critical_threshold_kw
                    else "high"
                )

                findings.append(
                    DetectedAnomalyFinding(
                        finding_id=f"FINDING-PEAK-CAP-H{idx:02d}",
                        scenario_id="ANOMALY_PEAK_THRESHOLD_003" if idx == 19 else None,
                        category="high_demand_period",
                        title="Factory Peak Demand Exceeding Grid Warning Threshold",
                        severity=severity,
                        affected_zone_id="facility_total",
                        affected_zone_name="Entire Facility",
                        affected_machine_id=None,
                        affected_machine_name=None,
                        interval_index=idx,
                        timestamp=ts,
                        evidence=AnomalyEvidence(
                            interval_index=idx,
                            timestamp=ts,
                            metric_name="total_factory_demand_kw",
                            observed_value=interval.total_factory_demand_kw,
                            baseline_threshold=145.0,
                            deviation_value=dev_val,
                            deviation_percent=dev_pct,
                            unit="kW",
                            grid_tariff_inr_per_kwh=tariff,
                        ),
                        detection_rule_id="RULE_PEAK_CAPACITY_RISK_03",
                        detection_rule_description=(
                            f"Total factory power ({interval.total_factory_demand_kw} kW) reached "
                            f"{round((interval.total_factory_demand_kw / contract_demand_kw) * 100, 1)}% of "
                            f"sanctioned contract demand ({contract_demand_kw} kW)."
                        ),
                        physical_hypothesis_notes=(
                            "Uncoordinated simultaneous startup of major inductive loads during shift handover "
                            f"coinciding with the peak tariff surcharge window (INR {tariff}/kWh)."
                        ),
                        estimated_financial_impact_inr=fin_impact,
                        suggested_action=(
                            "Reschedule high-power batch operations outside the 18:00-22:00 peak tariff window and stagger motor starts."
                        ),
                    )
                )

        return findings

    def get_anomalies(
        self,
        factory_id: str = DEFAULT_FACTORY_ID,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        zone_id: Optional[str] = None,
    ) -> AnomalyListResponse:
        """Retrieve detected anomaly findings with optional filtering for a given factory."""
        timeseries_resp = factory_data_service.get_timeseries(factory_id)
        profile_resp = factory_data_service.get_profile(factory_id)
        raw_profile = factory_data_service.get_raw_profile(factory_id)

        findings = self.detect_anomalies(timeseries_resp.intervals, raw_profile)

        # Apply filters
        filtered = findings
        if severity:
            sev_lower = severity.strip().lower()
            filtered = [f for f in filtered if f.severity.lower() == sev_lower]
        if category:
            cat_lower = category.strip().lower()
            filtered = [f for f in filtered if f.category.lower() == cat_lower]
        if zone_id:
            zid_lower = zone_id.strip().lower()
            filtered = [
                f for f in filtered if f.affected_zone_id and f.affected_zone_id.lower() == zid_lower
            ]

        # Calculate breakdowns across the full set of detected findings
        sev_counts: Dict[str, int] = {}
        for f in findings:
            sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1

        cat_counts: Dict[str, int] = {}
        for f in findings:
            cat_counts[f.category] = cat_counts.get(f.category, 0) + 1

        return AnomalyListResponse(
            total_detected=len(filtered),
            findings=filtered,
            severity_breakdown=sev_counts,
            category_breakdown=cat_counts,
            simulation_metadata=profile_resp.simulation_metadata,
        )

    def get_anomaly_by_id(
        self, anomaly_id: str, factory_id: str = DEFAULT_FACTORY_ID
    ) -> Optional[DetectedAnomalyFinding]:
        """Find a single anomaly by finding_id or scenario_id for the given factory."""
        timeseries_resp = factory_data_service.get_timeseries(factory_id)
        raw_profile = factory_data_service.get_raw_profile(factory_id)
        findings = self.detect_anomalies(timeseries_resp.intervals, raw_profile)

        id_clean = anomaly_id.strip().upper()
        # 1. Exact match by finding_id
        for f in findings:
            if f.finding_id.upper() == id_clean:
                return f
        # 2. Exact match by scenario_id
        for f in findings:
            if f.scenario_id and f.scenario_id.upper() == id_clean:
                return f
        # 3. Prefix match for backward compatibility (e.g. FINDING-SPIKE-H19 or FINDING-SPIKE-H11)
        for f in findings:
            if f.finding_id.upper().startswith(id_clean + "-"):
                return f
        return None


anomaly_detector_service = AnomalyDetectorService()

