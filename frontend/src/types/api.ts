/**
 * TypeScript type definitions for GridMind AI.
 * Mirrors the backend Pydantic models from Phases 1–5:
 * - Factory profile and 24h simulated time series (Phase 2)
 * - Energy metrics, analytical profile, and detected anomalies (Phase 3)
 * - Renewable energy allocation, baseline, and LP optimisation (Phase 4)
 * - Gemini AI investigation, evidence, and report schemas (Phase 5)
 */

export interface SimulationMetadata {
  is_synthetic: boolean;
  generation_seed: number;
  generated_at: string;
  dataset_version: string;
  disclaimer: string;
}

// -------------------------------------------------------------
// Phase 1: Health & Root
// -------------------------------------------------------------
export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  timestamp: string;
}

export interface AppInfoResponse {
  app_name: string;
  version: string;
  description: string;
  docs_url: string;
}

// -------------------------------------------------------------
// Phase 2: Factory Profile & Telemetry
// -------------------------------------------------------------
export interface MachineProfile {
  machine_id: string;
  name: string;
  rated_power_kw: number;
  idle_power_kw: number;
}

export interface ProductionZoneConfig {
  zone_id: string;
  name: string;
  description: string;
  base_power_kw: number;
  machines: MachineProfile[];
}

export interface SolarConfig {
  installed_capacity_kw: number;
  efficiency_factor: number;
  tracking: boolean;
}

export interface WindConfig {
  installed_capacity_kw: number;
  cut_in_speed_mps: number;
  rated_speed_mps: number;
}

export interface BiomassConfig {
  generator_capacity_kw: number;
  fuel_type: string;
  stock_kg: number;
  feedstock_conversion_rate_kg_per_kwh: number;
  marginal_cost_inr_per_kwh: number;
}

export interface TariffPeriodConfig {
  period_name: string;
  start_hour: number;
  end_hour: number;
  rate_inr_per_kwh: number;
}

export interface GridConfig {
  contract_demand_kw: number;
  voltage_kv: number;
  tariff_periods: TariffPeriodConfig[];
}

export interface ShiftSchedule {
  shift_name: string;
  start_hour: number;
  end_hour: number;
  is_operational: boolean;
}

export interface FactoryProfileResponse {
  factory_id: string;
  name: string;
  sector: string;
  location: string;
  currency: string;
  power_unit: string;
  energy_unit: string;
  production_unit: string;
  total_rated_connected_power_kw: number;
  facility_baseload_kw: number;
  zones: ProductionZoneConfig[];
  shifts: ShiftSchedule[];
  solar: SolarConfig;
  wind: WindConfig;
  biomass: BiomassConfig;
  grid: GridConfig;
  simulation_metadata: SimulationMetadata;
}

export interface FactoryListItem {
  factory_id: string;
  name: string;
  sector: string;
  location: string;
  total_rated_connected_power_kw: number;
  grid_contract_demand_kw: number;
  solar_capacity_kw: number;
  wind_capacity_kw: number;
  biomass_capacity_kw: number;
  demo_scenario_description: string;
}

export interface FactoryListResponse {
  total_factories: number;
  factories: FactoryListItem[];
  disclaimer: string;
}


export interface MachineReading {
  machine_id: string;
  power_kw: number;
  energy_kwh: number;
  is_running: boolean;
}

export interface ZoneReading {
  zone_id: string;
  power_kw: number;
  energy_kwh: number;
  is_active: boolean;
  machines: MachineReading[];
}

export interface GenerationAvailability {
  solar_kw: number;
  solar_kwh: number;
  wind_kw: number;
  wind_kwh: number;
  biomass_kw: number;
  biomass_kwh: number;
  total_renewable_available_kwh: number;
}

export interface GridData {
  tariff_rate_inr_per_kwh: number;
  is_peak_tariff: boolean;
  contract_demand_kw: number;
}

export interface IntervalMetadata {
  shift_name: string;
  is_production_active: boolean;
}

export interface TimeSeriesInterval {
  interval_index: number;
  timestamp: string;
  total_factory_demand_kw: number;
  total_factory_demand_kwh: number;
  production_output_units: number;
  zones: ZoneReading[];
  renewable_generation: GenerationAvailability;
  grid: GridData;
  metadata: IntervalMetadata;
}

export interface FactoryTimeSeriesResponse {
  factory_id: string;
  simulation_date: string;
  total_intervals: number;
  intervals: TimeSeriesInterval[];
  simulation_metadata: SimulationMetadata;
}

export interface FactoryOverviewResponse {
  factory_id: string;
  factory_name: string;
  simulation_date: string;
  total_demand_kwh: number;
  peak_demand_kw: number;
  peak_demand_interval: number;
  total_production_units: number;
  total_solar_available_kwh: number;
  total_wind_available_kwh: number;
  total_biomass_available_kwh: number;
  total_renewable_available_kwh: number;
  simulation_metadata: SimulationMetadata;
}

// -------------------------------------------------------------
// Phase 3: Energy Metrics & Anomaly Detection
// -------------------------------------------------------------
export interface DemandMetrics {
  total_demand_kwh: number;
  average_hourly_demand_kwh: number;
  average_power_kw: number;
  peak_power_kw: number;
  peak_power_interval_index: number;
  peak_power_timestamp: string;
  total_production_units: number;
  overall_energy_intensity_kwh_per_unit?: number | null;
}

export interface ZoneMetric {
  zone_id: string;
  zone_name: string;
  total_consumption_kwh: number;
  average_power_kw: number;
  peak_power_kw: number;
  percentage_of_total_demand: number;
  total_production_units: number;
  energy_intensity_kwh_per_unit?: number | null;
}

export interface ShiftMetric {
  shift_name: string;
  hours_count: number;
  total_consumption_kwh: number;
  average_demand_kw: number;
  percentage_of_total_demand: number;
  total_production_units: number;
}

export interface RenewableSourceAvailability {
  source: string;
  total_available_kwh: number;
  average_available_kw: number;
  peak_available_kw: number;
  installed_capacity_kw: number;
  capacity_factor_percent: number;
}

export interface RenewableAvailabilityMetrics {
  sources: RenewableSourceAvailability[];
  total_renewable_available_kwh: number;
  availability_to_demand_ratio_percent: number;
  disclaimer: string;
}

export interface TariffPeriodCost {
  period_name: string;
  tariff_rate_inr_per_kwh: number;
  hours_count: number;
  energy_demand_kwh: number;
  estimated_cost_inr: number;
  percentage_of_total_cost: number;
}

export interface GridCostBaseline {
  total_estimated_cost_inr: number;
  average_blended_rate_inr_per_kwh: number;
  period_breakdown: TariffPeriodCost[];
  grid_contract_demand_kw: number;
  max_demand_kw: number;
  exceeds_grid_capacity: boolean;
  capacity_headroom_kw: number;
  description: string;
}

export interface ProductionAnalysis {
  total_production_units: number;
  idle_or_unproductive_intervals: number[];
  idle_consumption_total_kwh: number;
}

export interface EnergyMetricsSummaryResponse {
  factory_id: string;
  factory_name: string;
  simulation_date: string;
  demand_metrics: DemandMetrics;
  zone_metrics: ZoneMetric[];
  shift_metrics: ShiftMetric[];
  renewable_availability: RenewableAvailabilityMetrics;
  grid_cost_baseline: GridCostBaseline;
  production_analysis: ProductionAnalysis;
  simulation_metadata: SimulationMetadata;
}

export interface AnomalyEvidence {
  interval_index: number;
  timestamp: string;
  metric_name: string;
  observed_value: number;
  baseline_threshold: number;
  deviation_value: number;
  deviation_percent: number;
  unit: string;
  grid_tariff_inr_per_kwh?: number | null;
}

export interface DetectedAnomalyFinding {
  finding_id: string;
  scenario_id?: string | null;
  category: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_zone_id?: string | null;
  affected_zone_name?: string | null;
  affected_machine_id?: string | null;
  affected_machine_name?: string | null;
  interval_index: number;
  timestamp: string;
  evidence: AnomalyEvidence;
  detection_rule_id: string;
  detection_rule_description: string;
  physical_hypothesis_notes: string;
  estimated_financial_impact_inr?: number | null;
  suggested_action: string;
  is_synthetic: boolean;
}

export interface AnomalyListResponse {
  total_detected: number;
  findings: DetectedAnomalyFinding[];
  severity_breakdown: Record<string, number>;
  category_breakdown: Record<string, number>;
  simulation_metadata: SimulationMetadata;
}

export interface HourlyAnalyticalProfileItem {
  interval_index: number;
  timestamp: string;
  factory_demand_kw: number;
  factory_demand_kwh: number;
  production_units: number;
  energy_intensity_kwh_per_unit?: number | null;
  solar_available_kwh: number;
  wind_available_kwh: number;
  biomass_available_kwh: number;
  total_renewable_available_kwh: number;
  grid_tariff_inr_per_kwh: number;
  grid_cost_baseline_inr: number;
  active_anomalies: string[];
  is_peak_tariff: boolean;
  shift_name: string;
  is_production_active: boolean;
}

export interface AnalyticalEnergyProfileResponse {
  factory_id: string;
  factory_name: string;
  simulation_date: string;
  total_intervals: number;
  hourly_profile: HourlyAnalyticalProfileItem[];
  summary_totals: Record<string, number>;
  simulation_metadata: SimulationMetadata;
}

// -------------------------------------------------------------
// Phase 4: Renewable Optimisation Engine
// -------------------------------------------------------------
export interface IntervalSourceAllocation {
  interval_index: number;
  timestamp: string;
  factory_demand_kwh: number;
  solar_available_kwh: number;
  solar_allocated_kwh: number;
  wind_available_kwh: number;
  wind_allocated_kwh: number;
  biomass_available_kwh: number;
  biomass_allocated_kwh: number;
  grid_allocated_kwh: number;
  renewable_allocated_total_kwh: number;
  grid_tariff_inr_per_kwh: number;
  source_operating_cost_inr: number;
  grid_tariff_cost_inr: number;
  interval_total_cost_inr: number;
  baseline_grid_cost_inr: number;
  interval_savings_inr: number;
  unmet_demand_kwh: number;
  active_constraints: string[];
  energy_balance_error: number;
  is_feasible: boolean;
}

export interface SourceUtilizationSummary {
  source: string;
  total_available_kwh: number;
  total_allocated_kwh: number;
  utilization_rate_percent: number;
  total_cost_inr: number;
  effective_cost_per_kwh_inr: number;
}

export interface OptimizationSummaryResponse {
  factory_id: string;
  simulation_date: string;
  is_feasible: boolean;
  solver_status: string;
  total_demand_kwh: number;
  total_demand_served_kwh: number;
  unmet_demand_total_kwh: number;
  baseline_grid_only_cost_inr: number;
  optimised_supply_cost_inr: number;
  estimated_savings_inr: number;
  estimated_savings_percentage: number;
  renewable_energy_allocated_kwh: number;
  renewable_allocation_percentage: number;
  grid_energy_allocated_kwh: number;
  grid_energy_share_percentage: number;
  peak_grid_power_kw: number;
  peak_grid_contract_utilisation_percent: number;
  biomass_energy_consumed_kwh: number;
  biomass_fuel_consumed_kg: number;
  biomass_remaining_fuel_budget_kg: number;
  infeasible_intervals_count: number;
  production_fulfilment_units?: number | null;
  baseline_is_capacity_feasible?: boolean;
  active_scenario_name?: string;
  solar_multiplier?: number;
  tariff_multiplier?: number;
  disclaimer?: string;
  simulation_metadata: SimulationMetadata;
}

export interface OptimizationRunResponse extends OptimizationSummaryResponse {
  intervals: IntervalSourceAllocation[];
  source_breakdown: SourceUtilizationSummary[];
}

export interface HourlyBaselineItem {
  interval_index: number;
  timestamp: string;
  demand_kwh: number;
  demand_kw: number;
  grid_tariff_inr_per_kwh: number;
  baseline_cost_inr: number;
  is_peak_tariff: boolean;
  exceeds_grid_capacity: boolean;
}

export interface OptimizationBaselineResponse {
  factory_id: string;
  simulation_date: string;
  total_factory_demand_kwh: number;
  grid_contract_demand_kw: number;
  is_capacity_feasible: boolean;
  peak_factory_demand_kw: number;
  total_baseline_cost_inr: number;
  average_blended_rate_inr_per_kwh: number;
  hourly_baseline: HourlyBaselineItem[];
  simulation_metadata: SimulationMetadata;
}

// -------------------------------------------------------------
// Phase 5: Gemini AI Investigation
// -------------------------------------------------------------
export type InvestigationPriority = 'low' | 'medium' | 'high' | 'critical';
export type InvestigationStatus = 'completed' | 'failed' | 'unavailable' | 'partial';

export interface RecommendedAction {
  priority: InvestigationPriority;
  action: string;
  rationale: string;
  expected_operational_benefit: string;
  safety_considerations: string;
  verification_step: string;
}

export interface PossibleCause {
  hypothesis: string;
  likelihood: string;
  supporting_evidence: string;
  is_confirmed: boolean;
}

export interface FinancialImpactSummary {
  detected_excess_energy_kwh?: number | null;
  excess_energy_grid_cost_inr?: number | null;
  grid_only_baseline_cost_inr?: number | null;
  optimised_scenario_cost_inr?: number | null;
  estimated_daily_savings_inr?: number | null;
  financial_caveats: string;
}

export interface InvestigationEvidencePayload {
  anomaly_id: string;
  interval_index: number;
  timestamp: string;
  category: string;
  severity: string;
  metric_name: string;
  observed_value: number;
  baseline_threshold: number;
  deviation_value: number;
  deviation_percent: number;
  unit: string;
  detection_rule_id: string;
  detection_rule_description: string;
  affected_zone_name?: string | null;
  affected_machine_name?: string | null;
  grid_tariff_inr_per_kwh?: number | null;
}

export interface InvestigationAiMetadata {
  model_name: string;
  provider: string;
  is_mocked: boolean;
  latency_ms?: number | null;
  tokens_used?: number | null;
  temperature: number;
}

export interface InvestigationResponse {
  investigation_id: string;
  anomaly_id: string;
  status: InvestigationStatus;
  summary: string;
  observations: string[];
  evidence: InvestigationEvidencePayload;
  possible_causes: PossibleCause[];
  recommended_actions: RecommendedAction[];
  financial_impact: FinancialImpactSummary;
  uncertainties: string[];
  follow_up_checks: string[];
  simulation_metadata: SimulationMetadata;
  ai_metadata: InvestigationAiMetadata;
}

export interface InvestigationStatusResponse {
  is_configured: boolean;
  model_name: string;
  is_available: boolean;
  status_message: string;
  supported_modes: string[];
}

export interface FailedInvestigationItem {
  anomaly_id: string;
  error_message: string;
}

export interface InvestigationReportResponse {
  report_id: string;
  generated_at: string;
  total_anomalies_evaluated: number;
  successful_investigations_count: number;
  failed_investigations_count: number;
  overall_risk_summary: string;
  investigations: InvestigationResponse[];
  partial_failures: FailedInvestigationItem[];
  prioritized_actions: RecommendedAction[];
  optimization_context?: {
    baseline_grid_only_cost_inr: number;
    optimised_supply_cost_inr: number;
    estimated_savings_inr: number;
    renewable_allocation_percentage: number;
  } | null;
  simulation_metadata: SimulationMetadata;
  ai_metadata: InvestigationAiMetadata;
}
