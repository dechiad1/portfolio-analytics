import type { ApiError } from '../types';

/**
 * Base URL for API requests, configured via environment variable.
 */
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Storage key for session ID.
 */
const SESSION_STORAGE_KEY = 'portfolio_analytics_session_id';

/**
 * Storage key for JWT token.
 */
const TOKEN_STORAGE_KEY = 'portfolio_analytics_token';

/**
 * Get the stored session ID from localStorage.
 */
export function getStoredSessionId(): string | null {
  return localStorage.getItem(SESSION_STORAGE_KEY);
}

/**
 * Store the session ID in localStorage.
 */
export function setStoredSessionId(sessionId: string): void {
  localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

/**
 * Clear the stored session ID from localStorage.
 */
export function clearStoredSessionId(): void {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

/**
 * Get the stored JWT token from localStorage.
 */
export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

/**
 * Store the JWT token in localStorage.
 */
export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

/**
 * Clear the stored JWT token from localStorage.
 */
export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

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
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  sessionId?: string | null;
  token?: string | null;
  headers?: Record<string, string>;
  skipAuth?: boolean;
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
  const { method = 'GET', body, sessionId, token, headers: customHeaders = {}, skipAuth = false } = options;

  const headers: Record<string, string> = {
    ...customHeaders,
  };

  // Add session ID header if provided
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }

  // Add Authorization header if token provided or from storage (unless skipAuth)
  if (!skipAuth) {
    const authToken = token ?? getStoredToken();
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
  }

  // Add content-type for JSON body
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const config: RequestInit = {
    method,
    headers,
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
 * Options for API convenience methods.
 */
interface ApiOptions {
  sessionId?: string | null;
  token?: string | null;
  skipAuth?: boolean;
}

/**
 * Convenience methods for common HTTP operations.
 */
export const api = {
  get: <T>(endpoint: string, options?: ApiOptions | string | null) => {
    // Support legacy sessionId parameter
    const opts = typeof options === 'string' || options === null
      ? { sessionId: options }
      : options;
    return apiRequest<T>(endpoint, { method: 'GET', ...opts });
  },

  post: <T>(endpoint: string, body?: unknown, options?: ApiOptions | string | null) => {
    const opts = typeof options === 'string' || options === null
      ? { sessionId: options }
      : options;
    return apiRequest<T>(endpoint, { method: 'POST', body, ...opts });
  },

  put: <T>(endpoint: string, body?: unknown, options?: ApiOptions | string | null) => {
    const opts = typeof options === 'string' || options === null
      ? { sessionId: options }
      : options;
    return apiRequest<T>(endpoint, { method: 'PUT', body, ...opts });
  },

  delete: <T>(endpoint: string, options?: ApiOptions | string | null) => {
    const opts = typeof options === 'string' || options === null
      ? { sessionId: options }
      : options;
    return apiRequest<T>(endpoint, { method: 'DELETE', ...opts });
  },

  /**
   * Upload a file using multipart form data.
   */
  upload: <T>(endpoint: string, file: File, fieldName: string, options?: ApiOptions | string | null) => {
    const opts = typeof options === 'string' || options === null
      ? { sessionId: options }
      : options;
    const formData = new FormData();
    formData.append(fieldName, file);
    return apiRequest<T>(endpoint, {
      method: 'POST',
      body: formData,
      ...opts,
    });
  },
};
