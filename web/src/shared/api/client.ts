import type { ApiError } from '../types';

/**
 * Base URL for API requests, configured via environment variable.
 */
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors.
 */
export class ApiClientError extends Error {
  public readonly status: number;
  public readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiClientError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Request options for the API client.
 */
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: unknown;
  headers?: Record<string, string>;
}

/**
 * Parse error response from the API.
 */
async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const data = await response.json();
    return {
      detail: data.detail || data.message || 'An error occurred',
      status: response.status,
    };
  } catch {
    return {
      detail: response.statusText || 'An error occurred',
      status: response.status,
    };
  }
}

/**
 * Make an API request with automatic JSON handling and error parsing.
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = 'GET', body, headers: customHeaders = {} } = options;

  const headers: Record<string, string> = {
    ...customHeaders,
  };

  // Add content-type for JSON body
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const config: RequestInit = {
    method,
    headers,
    credentials: 'include',
  };

  // Add body for non-GET requests
  if (body) {
    config.body = body instanceof FormData ? body : JSON.stringify(body);
  }

  const url = `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, config);

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    // Handle non-2xx responses
    if (!response.ok) {
      const error = await parseErrorResponse(response);
      throw new ApiClientError(error.status, error.detail);
    }

    // Parse JSON response
    const data = await response.json();
    return data as T;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    // Network or other errors
    throw new ApiClientError(0, error instanceof Error ? error.message : 'Network error');
  }
}

/**
 * Convenience methods for common HTTP operations.
 */
export const api = {
  get: <T>(endpoint: string) => {
    return apiRequest<T>(endpoint, { method: 'GET' });
  },

  post: <T>(endpoint: string, body?: unknown) => {
    return apiRequest<T>(endpoint, { method: 'POST', body });
  },

  put: <T>(endpoint: string, body?: unknown) => {
    return apiRequest<T>(endpoint, { method: 'PUT', body });
  },

  delete: <T>(endpoint: string) => {
    return apiRequest<T>(endpoint, { method: 'DELETE' });
  },

  patch: <T>(endpoint: string, body?: unknown) => {
    return apiRequest<T>(endpoint, { method: 'PATCH', body });
  },

  upload: <T>(endpoint: string, file: File, fieldName: string) => {
    const formData = new FormData();
    formData.append(fieldName, file);
    return apiRequest<T>(endpoint, {
      method: 'POST',
      body: formData,
    });
  },
};
