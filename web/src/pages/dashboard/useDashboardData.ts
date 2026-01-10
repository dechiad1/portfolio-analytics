import { useState, useEffect, useCallback } from 'react';
import type { PortfolioAnalytics } from '../../shared/types';
import { useSession } from '../../shared/hooks/useSession';
import { ApiClientError } from '../../shared/api/client';
import { fetchAnalytics } from './dashboardApi';

/**
 * State and operations for dashboard analytics data.
 */
interface DashboardDataState {
  /** Analytics data from the API */
  analytics: PortfolioAnalytics | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if fetch failed */
  error: string | null;
  /** Refetch analytics from the server */
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch and manage dashboard analytics data.
 */
export function useDashboardData(): DashboardDataState {
  const { sessionId } = useSession();
  const [analytics, setAnalytics] = useState<PortfolioAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchAnalytics(sessionId);
      setAnalytics(data);
    } catch (err) {
      const message = err instanceof ApiClientError
        ? err.detail
        : 'Failed to load analytics';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const refetch = useCallback(async () => {
    await loadAnalytics();
  }, [loadAnalytics]);

  return {
    analytics,
    isLoading,
    error,
    refetch,
  };
}
