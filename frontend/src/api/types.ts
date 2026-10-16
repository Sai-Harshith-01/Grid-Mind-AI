/**
 * Type definitions for GridMind AI Backend API responses.
 */

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface AppInfoResponse {
  name: string;
  description: string;
  version: string;
  docs_url: string;
}

export type HealthCheckState =
  | { status: 'loading' }
  | { status: 'online'; data: HealthResponse }
  | { status: 'offline'; error: string; timestamp: string };
