/**
 * GridMind AI API Service Layer.
 * Typed caller functions for all backend endpoints across Phases 1–5 with full Multi-Factory support.
 */

import { getJson, postJson } from './client';
import {
  HealthResponse,
  AppInfoResponse,
  FactoryListResponse,
  FactoryProfileResponse,
  FactoryTimeSeriesResponse,
  FactoryOverviewResponse,
  EnergyMetricsSummaryResponse,
  AnalyticalEnergyProfileResponse,
  AnomalyListResponse,
  DetectedAnomalyFinding,
  OptimizationBaselineResponse,
  OptimizationSummaryResponse,
  OptimizationRunResponse,
  InvestigationStatusResponse,
  InvestigationResponse,
  InvestigationReportResponse,
} from '../types/api';

// -------------------------------------------------------------
// Phase 1: Health & Root
// -------------------------------------------------------------
export async function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>('/health');
}

export async function fetchAppInfo(): Promise<AppInfoResponse> {
  return getJson<AppInfoResponse>('/');
}

// -------------------------------------------------------------
// Multi-Factory Registry & Synthetic Telemetry
// -------------------------------------------------------------
export async function fetchFactories(): Promise<FactoryListResponse> {
  return getJson<FactoryListResponse>('/api/factories');
}

export async function fetchFactoryProfile(factoryId?: string): Promise<FactoryProfileResponse> {
  const qs = factoryId ? `?factory_id=${encodeURIComponent(factoryId)}` : '';
  return getJson<FactoryProfileResponse>(`/api/factory/profile${qs}`);
}

export async function fetchFactoryTimeseries(factoryId?: string): Promise<FactoryTimeSeriesResponse> {
  const qs = factoryId ? `?factory_id=${encodeURIComponent(factoryId)}` : '';
  return getJson<FactoryTimeSeriesResponse>(`/api/factory/timeseries${qs}`);
}

export async function fetchFactoryOverview(factoryId?: string): Promise<FactoryOverviewResponse> {
  const qs = factoryId ? `?factory_id=${encodeURIComponent(factoryId)}` : '';
  return getJson<FactoryOverviewResponse>(`/api/factory/overview${qs}`);
}

// -------------------------------------------------------------
// Phase 3: Energy Analytics & Anomaly Detection
// -------------------------------------------------------------
export async function fetchEnergyMetrics(factoryId?: string): Promise<EnergyMetricsSummaryResponse> {
  const qs = factoryId ? `?factory_id=${encodeURIComponent(factoryId)}` : '';
  return getJson<EnergyMetricsSummaryResponse>(`/api/analysis/metrics${qs}`);
}

export async function fetchAnalyticalProfile(factoryId?: string): Promise<AnalyticalEnergyProfileResponse> {
  const qs = factoryId ? `?factory_id=${encodeURIComponent(factoryId)}` : '';
  return getJson<AnalyticalEnergyProfileResponse>(`/api/analysis/energy-profile${qs}`);
}

export async function fetchAnomalies(params?: {
  factory_id?: string;
  severity?: string;
  category?: string;
  zone_id?: string;
}): Promise<AnomalyListResponse> {
  const query = new URLSearchParams();
  if (params?.factory_id) query.append('factory_id', params.factory_id);
  if (params?.severity) query.append('severity', params.severity);
  if (params?.category) query.append('category', params.category);
  if (params?.zone_id) query.append('zone_id', params.zone_id);

  const qs = query.toString();
  return getJson<AnomalyListResponse>(`/api/analysis/anomalies${qs ? `?${qs}` : ''}`);
}

export async function fetchAnomalyDetail(anomalyId: string, factoryId?: string): Promise<DetectedAnomalyFinding> {
  const qs = factoryId ? `?factory_id=${encodeURIComponent(factoryId)}` : '';
  return getJson<DetectedAnomalyFinding>(`/api/analysis/anomalies/${encodeURIComponent(anomalyId)}${qs}`);
}

// -------------------------------------------------------------
// Phase 4: Renewable Optimisation Engine
// -------------------------------------------------------------
export interface OptimizationScenarioParams {
  solarMultiplier?: number;
  tariffMultiplier?: number;
}

export async function fetchOptimizationBaseline(
  factoryId?: string,
  params?: { tariffMultiplier?: number }
): Promise<OptimizationBaselineResponse> {
  const query = new URLSearchParams();
  if (factoryId) query.append('factory_id', factoryId);
  if (params?.tariffMultiplier !== undefined) query.append('tariff_multiplier', params.tariffMultiplier.toString());
  const qs = query.toString();
  return getJson<OptimizationBaselineResponse>(`/api/optimization/baseline${qs ? `?${qs}` : ''}`);
}

export async function fetchOptimizationSummary(
  factoryId?: string,
  params?: OptimizationScenarioParams
): Promise<OptimizationSummaryResponse> {
  const query = new URLSearchParams();
  if (factoryId) query.append('factory_id', factoryId);
  if (params?.solarMultiplier !== undefined) query.append('solar_multiplier', params.solarMultiplier.toString());
  if (params?.tariffMultiplier !== undefined) query.append('tariff_multiplier', params.tariffMultiplier.toString());
  const qs = query.toString();
  return getJson<OptimizationSummaryResponse>(`/api/optimization/summary${qs ? `?${qs}` : ''}`);
}

export async function runOptimization(
  factoryId?: string,
  params?: OptimizationScenarioParams
): Promise<OptimizationRunResponse> {
  const query = new URLSearchParams();
  if (factoryId) query.append('factory_id', factoryId);
  if (params?.solarMultiplier !== undefined) query.append('solar_multiplier', params.solarMultiplier.toString());
  if (params?.tariffMultiplier !== undefined) query.append('tariff_multiplier', params.tariffMultiplier.toString());
  const qs = query.toString();
  return getJson<OptimizationRunResponse>(`/api/optimization/run${qs ? `?${qs}` : ''}`);
}

// -------------------------------------------------------------
// Phase 5: Gemini AI Energy Waste Investigation
// -------------------------------------------------------------
export async function fetchInvestigationStatus(): Promise<InvestigationStatusResponse> {
  return getJson<InvestigationStatusResponse>('/api/investigation/status');
}

export async function investigateAnomaly(anomalyId: string, factoryId?: string): Promise<InvestigationResponse> {
  const qs = factoryId ? `?factory_id=${encodeURIComponent(factoryId)}` : '';
  return postJson<InvestigationResponse>(`/api/investigation/anomaly/${encodeURIComponent(anomalyId)}${qs}`);
}

export async function generateInvestigationReport(
  request?: {
    max_findings?: number;
    min_severity?: string;
  },
  factoryId?: string
): Promise<InvestigationReportResponse> {
  const qs = factoryId ? `?factory_id=${encodeURIComponent(factoryId)}` : '';
  return postJson<InvestigationReportResponse>(
    `/api/investigation/report${qs}`,
    request || { max_findings: 5 }
  );
}
