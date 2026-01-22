import { useState, useEffect, useCallback } from 'react';
import { ApiClientError } from '../../shared/api/client';
import { fetchSecurities, type Security } from './securitiesApi';

/**
 * State and operations for managing the securities list.
 */
interface SecuritiesState {
  /** List of all securities */
  securities: Security[];
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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSecurities = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchSecurities();
      setSecurities(data);
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
    isLoading,
    error,
    refetch,
    clearError,
  };
}
