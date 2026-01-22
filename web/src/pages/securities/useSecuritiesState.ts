import { useState, useEffect, useCallback } from 'react';
import { ApiClientError } from '../../shared/api/client';
import {
  fetchSecurities,
  fetchUserAddedTickers,
  type Security,
  type UserAddedTicker,
} from './securitiesApi';

/**
 * State and operations for managing the securities list.
 */
interface SecuritiesState {
  /** List of all securities */
  securities: Security[];
  /** List of user-added tickers (may not have data yet) */
  userAddedTickers: UserAddedTicker[];
  /** Loading state for initial fetch */
  isLoading: boolean;
  /** Error message from last operation */
  error: string | null;
  /** Refetch securities from the server */
  refetch: () => Promise<void>;
  /** Clear current error */
  clearError: () => void;
}

/**
 * Hook to manage securities list state.
 */
export function useSecuritiesState(): SecuritiesState {
  const [securities, setSecurities] = useState<Security[]>([]);
  const [userAddedTickers, setUserAddedTickers] = useState<UserAddedTicker[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSecurities = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch both in parallel
      const [securitiesData, userAddedData] = await Promise.all([
        fetchSecurities(),
        fetchUserAddedTickers(),
      ]);
      setSecurities(securitiesData);
      setUserAddedTickers(userAddedData);
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.detail : 'Failed to load securities';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSecurities();
  }, [loadSecurities]);

  const refetch = useCallback(async () => {
    await loadSecurities();
  }, [loadSecurities]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    securities,
    userAddedTickers,
    isLoading,
    error,
    refetch,
    clearError,
  };
}
