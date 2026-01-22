import { useState, useEffect, useCallback } from 'react';
import type { PortfolioWithUser, PortfolioInput } from '../../shared/types';
import { ApiClientError } from '../../shared/api/client';
import { fetchAllPortfolios, createPortfolio, deletePortfolio } from './portfolioApi';

/**
 * State and operations for managing the portfolio list.
 */
interface PortfolioListState {
  /** List of all portfolios with user info */
  portfolios: PortfolioWithUser[];
  /** Loading state for initial fetch */
  isLoading: boolean;
  /** Error message from last operation */
  error: string | null;
  /** Whether a mutation is in progress */
  isMutating: boolean;
  /** Refetch portfolios from the server */
  refetch: () => Promise<void>;
  /** Create a new portfolio */
  addPortfolio: (input: PortfolioInput) => Promise<boolean>;
  /** Delete a portfolio */
  removePortfolio: (portfolioId: string) => Promise<boolean>;
  /** Clear current error */
  clearError: () => void;
}

/**
 * Hook to manage portfolio list state and operations.
 */
export function usePortfolioListState(): PortfolioListState {
  const [portfolios, setPortfolios] = useState<PortfolioWithUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);

  const loadPortfolios = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchAllPortfolios();
      setPortfolios(data);
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.detail : 'Failed to load portfolios';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPortfolios();
  }, [loadPortfolios]);

  const refetch = useCallback(async () => {
    await loadPortfolios();
  }, [loadPortfolios]);

  const addPortfolio = useCallback(async (input: PortfolioInput): Promise<boolean> => {
    setIsMutating(true);
    setError(null);

    try {
      await createPortfolio(input);
      await loadPortfolios();
      return true;
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.detail : 'Failed to create portfolio';
      setError(message);
      return false;
    } finally {
      setIsMutating(false);
    }
  }, [loadPortfolios]);

  const removePortfolio = useCallback(async (portfolioId: string): Promise<boolean> => {
    setIsMutating(true);
    setError(null);

    try {
      await deletePortfolio(portfolioId);
      setPortfolios((prev) => prev.filter((p) => p.id !== portfolioId));
      return true;
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.detail : 'Failed to delete portfolio';
      setError(message);
      return false;
    } finally {
      setIsMutating(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    portfolios,
    isLoading,
    error,
    isMutating,
    refetch,
    addPortfolio,
    removePortfolio,
    clearError,
  };
}
