import { api } from './client';
import type {
  User,
  AuthTokens,
  LoginCredentials,
  RegisterCredentials,
} from '../types';

/**
 * Register a new user.
 */
export async function register(credentials: RegisterCredentials): Promise<AuthTokens> {
  return api.post<AuthTokens>('/auth/register', credentials, { skipAuth: true });
}

/**
 * Login with email and password.
 */
export async function login(credentials: LoginCredentials): Promise<AuthTokens> {
  return api.post<AuthTokens>('/auth/login', credentials, { skipAuth: true });
}

/**
 * Get the current authenticated user.
 */
export async function getCurrentUser(): Promise<User> {
  return api.get<User>('/auth/me');
}
