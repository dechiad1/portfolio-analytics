import {
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import { ApiClientError } from '../api/client';
import { getCurrentUser, logout as apiLogout } from '../api/authApi';
import { AuthContext } from './authContextDef';
import type { User } from '../types';

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * AuthProvider manages OAuth authentication state via session cookies.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 401) {
        setUser(null);
      }
    }
  }, []);

  // Initialize auth state by checking session cookie
  useEffect(() => {
    const initializeAuth = async () => {
      await refreshUser();
      setIsLoading(false);
    };

    initializeAuth();
  }, [refreshUser]);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      // Ignore logout errors
    }
    setUser(null);
    window.location.href = '/login';
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      logout,
      refreshUser,
    }),
    [user, isLoading, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
