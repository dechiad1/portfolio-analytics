import { api } from './client';
import type { User } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

/**
 * Get the OAuth login URL (redirects to IDP).
 */
export function getOAuthLoginUrl(): string {
  return `${API_URL}/oauth/login`;
}

/**
 * Logout - clears session cookie via API.
 */
export async function logout(): Promise<void> {
  return api.post<void>('/oauth/logout');
}

/**
 * Get the current authenticated user (from session cookie).
 */
export async function getCurrentUser(): Promise<User> {
  return api.get<User>('/oauth/me');
}
