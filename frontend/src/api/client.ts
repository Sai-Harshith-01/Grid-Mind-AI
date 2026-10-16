/**
 * GridMind API Client
 * Centralized API configuration and typed HTTP fetch utilities.
 * Configured via Vite environment variable VITE_API_BASE_URL with fallback to http://localhost:8000.
 */

export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL?.trim() || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public statusText?: string,
    public detail?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detailMessage = response.statusText;
    try {
      const errorJson = await response.json();
      if (errorJson && typeof errorJson === 'object' && errorJson.detail) {
        detailMessage = typeof errorJson.detail === 'string' 
          ? errorJson.detail 
          : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Body was not JSON
    }

    throw new ApiError(
      detailMessage || `HTTP ${response.status} (${response.statusText})`,
      response.status,
      response.statusText,
      detailMessage
    );
  }

  return (await response.json()) as T;
}

/**
 * Generic typed HTTP GET request handler.
 */
export async function getJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Unknown network failure';
    throw new ApiError(`Connection failed: ${message}`);
  }
}

/**
 * Generic typed HTTP POST request handler.
 */
export async function postJson<T>(
  endpoint: string,
  body?: unknown,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options?.headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      ...options,
    });

    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Unknown network failure';
    throw new ApiError(`Connection failed: ${message}`);
  }
}
