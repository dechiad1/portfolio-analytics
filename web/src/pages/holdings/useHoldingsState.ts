import { useState, useEffect, useCallback } from 'react';
import type { Holding, HoldingInput } from '../../shared/types';
import { ApiClientError } from '../../shared/api/client';
import {
  fetchHoldings,
  createHolding,
  updateHolding,
  deleteHolding,
  uploadHoldingsCsv,
} from './holdingsApi';

/**
 * State and operations for managing holdings.
 */
interface HoldingsState {
  /** List of all holdings */
  holdings: Holding[];
  /** Loading state for initial fetch */
  isLoading: boolean;
  /** Error message from last operation */
  error: string | null;
  /** Whether a mutation is in progress */
  isMutating: boolean;
  /** Refetch holdings from the server */
  refetch: () => Promise<void>;
  /** Add a new holding */
  addHolding: (holding: HoldingInput) => Promise<boolean>;
  /** Update an existing holding */
  editHolding: (holdingId: string, holding: HoldingInput) => Promise<boolean>;
  /** Delete a holding */
  removeHolding: (holdingId: string) => Promise<boolean>;
  /** Upload a CSV file of holdings */
  uploadCsv: (file: File) => Promise<{ success: boolean; count?: number; error?: string }>;
  /** Clear current error */
  clearError: () => void;
}

/**
 * Hook to manage holdings state and operations.
 */
export function useHoldingsState(): HoldingsState {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);

  const loadHoldings = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchHoldings();
      setHoldings(data);
    } catch (err) {
      const message = err instanceof ApiClientError
        ? err.detail
        : 'Failed to load holdings';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHoldings();
  }, [loadHoldings]);

  const refetch = useCallback(async () => {
    await loadHoldings();
  }, [loadHoldings]);

  const addHolding = useCallback(async (holding: HoldingInput): Promise<boolean> => {
    setIsMutating(true);
    setError(null);

    try {
      const newHolding = await createHolding(holding);
      setHoldings((prev) => [...prev, newHolding]);
      return true;
    } catch (err) {
      const message = err instanceof ApiClientError
        ? err.detail
        : 'Failed to add holding';
      setError(message);
      return false;
    } finally {
      setIsMutating(false);
    }
  }, []);

  const editHolding = useCallback(
    async (holdingId: string, holding: HoldingInput): Promise<boolean> => {
      setIsMutating(true);
      setError(null);

      try {
        const updatedHolding = await updateHolding(holdingId, holding);
        setHoldings((prev) =>
          prev.map((h) => (h.id === holdingId ? updatedHolding : h))
        );
        return true;
      } catch (err) {
        const message = err instanceof ApiClientError
          ? err.detail
          : 'Failed to update holding';
        setError(message);
        return false;
      } finally {
        setIsMutating(false);
      }
    },
    []
  );

  const removeHolding = useCallback(
    async (holdingId: string): Promise<boolean> => {
      setIsMutating(true);
      setError(null);

      try {
        await deleteHolding(holdingId);
        setHoldings((prev) => prev.filter((h) => h.id !== holdingId));
        return true;
      } catch (err) {
        const message = err instanceof ApiClientError
          ? err.detail
          : 'Failed to delete holding';
        setError(message);
        return false;
      } finally {
        setIsMutating(false);
      }
    },
    []
  );

  const uploadCsv = useCallback(
    async (file: File): Promise<{ success: boolean; count?: number; error?: string }> => {
      setIsMutating(true);
      setError(null);

      try {
        const newHoldings = await uploadHoldingsCsv(file);
        setHoldings((prev) => [...prev, ...newHoldings]);
        return { success: true, count: newHoldings.length };
      } catch (err) {
        const message = err instanceof ApiClientError
          ? err.detail
          : 'Failed to upload CSV';
        setError(message);
        return { success: false, error: message };
      } finally {
        setIsMutating(false);
      }
    },
    []
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    holdings,
    isLoading,
    error,
    isMutating,
    refetch,
    addHolding,
    editHolding,
    removeHolding,
    uploadCsv,
    clearError,
  };
}
