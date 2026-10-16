import { getJson } from './client';
import { HealthResponse, AppInfoResponse } from './types';

/**
 * Fetch backend system health status.
 * Target: GET /health
 */
export async function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>('/health');
}

/**
 * Fetch root application metadata.
 * Target: GET /
 */
export async function fetchAppInfo(): Promise<AppInfoResponse> {
  return getJson<AppInfoResponse>('/');
}
