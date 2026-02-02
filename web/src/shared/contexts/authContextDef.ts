import { createContext } from 'react';
import type { User } from '../types';

/**
 * Auth state and operations for OAuth-based authentication.
 */
export interface AuthState {
  /** Current authenticated user */
  user: User | null;
  /** Whether auth is being initialized */
  isLoading: boolean;
  /** Whether user is authenticated */
  isAuthenticated: boolean;
  /** Logout the current user */
  logout: () => Promise<void>;
  /** Refresh user data from server */
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthState | null>(null);
