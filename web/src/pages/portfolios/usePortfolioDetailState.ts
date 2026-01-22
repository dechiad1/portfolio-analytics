import { useState, useEffect, useCallback } from 'react';
import type {
  Portfolio,
  PortfolioSummary,
  PortfolioHolding,
  PortfolioHoldingInput,
  RiskAnalysisResult,
} from '../../shared/types';
import { ApiClientError } from '../../shared/api/client';
import {
  getPortfolio,
  getPortfolioSummary,
  fetchPortfolioHoldings,
  addPortfolioHolding,
  updatePortfolioHolding,
  deletePortfolioHolding,
  generateRiskAnalysis,
} from './portfolioApi';

/**
 * State and operations for portfolio detail page.
 */
interface PortfolioDetailState {
  /** Portfolio data */
  portfolio: Portfolio | null;
  /** Portfolio summary */
  summary: PortfolioSummary | null;
  /** Portfolio holdings */
  holdings: PortfolioHolding[];
  /** Risk analysis result */
  riskAnalysis: RiskAnalysisResult | null;
  /** Loading state for initial fetch */
  isLoading: boolean;
  /** Error message from last operation */
  error: string | null;
  /** Whether a mutation is in progress */
  isMutating: boolean;
  /** Whether risk analysis is being generated */
  isGeneratingRiskAnalysis: boolean;
  /** Refetch all data */
  refetch: () => Promise<void>;
  /** Add a new holding */
  addHolding: (input: PortfolioHoldingInput) => Promise<boolean>;
  /** Update an existing holding */
  editHolding: (holdingId: string, input: PortfolioHoldingInput) => Promise<boolean>;
  /** Delete a holding */
  removeHolding: (holdingId: string) => Promise<boolean>;
  /** Generate risk analysis */
  runRiskAnalysis: () => Promise<boolean>;
  /** Clear current error */
  clearError: () => void;
}

/**
 * Hook to manage portfolio detail state and operations.
 */
export function usePortfolioDetailState(portfolioId: string): PortfolioDetailState {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [riskAnalysis, setRiskAnalysis] = useState<RiskAnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [isGeneratingRiskAnalysis, setIsGeneratingRiskAnalysis] = useState(false);

  const loadPortfolioData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch portfolio first to check access
      const portfolioData = await getPortfolio(portfolioId);
      setPortfolio(portfolioData);

      // Then fetch related data in parallel
      const [summaryData, holdingsData] = await Promise.all([
        getPortfolioSummary(portfolioId).catch(() => null),
        fetchPortfolioHoldings(portfolioId).catch(() => []),
      ]);

      setSummary(summaryData);
      setHoldings(holdingsData);
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 403) {
          setError('Access denied. You do not have permission to view this portfolio.');
        } else if (err.status === 404) {
          setError('Portfolio not found.');
        } else {
          setError(err.detail);
        }
      } else {
        setError('Failed to load portfolio');
      }
    } finally {
      setIsLoading(false);
    }
  }, [portfolioId]);

  useEffect(() => {
    loadPortfolioData();
  }, [loadPortfolioData]);

  const refetch = useCallback(async () => {
    await loadPortfolioData();
  }, [loadPortfolioData]);

  const refreshSummary = useCallback(async () => {
    try {
      const summaryData = await getPortfolioSummary(portfolioId);
      setSummary(summaryData);
    } catch {
      // Silently fail summary refresh, it's not critical
    }
  }, [portfolioId]);

  const addHolding = useCallback(
    async (input: PortfolioHoldingInput): Promise<boolean> => {
      setIsMutating(true);
      setError(null);

      try {
        const newHolding = await addPortfolioHolding(portfolioId, input);
        setHoldings((prev) => [...prev, newHolding]);
        // Refresh summary after adding holding
        refreshSummary();
        return true;
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to add holding';
        setError(message);
        return false;
      } finally {
        setIsMutating(false);
      }
    },
    [portfolioId, refreshSummary]
  );

  const editHolding = useCallback(
    async (holdingId: string, input: PortfolioHoldingInput): Promise<boolean> => {
      setIsMutating(true);
      setError(null);

      try {
        const updatedHolding = await updatePortfolioHolding(portfolioId, holdingId, input);
        setHoldings((prev) =>
          prev.map((h) => (h.id === holdingId ? updatedHolding : h))
        );
        // Refresh summary after updating holding
        refreshSummary();
        return true;
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to update holding';
        setError(message);
        return false;
      } finally {
        setIsMutating(false);
      }
    },
    [portfolioId, refreshSummary]
  );

  const removeHolding = useCallback(
    async (holdingId: string): Promise<boolean> => {
      setIsMutating(true);
      setError(null);

      try {
        await deletePortfolioHolding(portfolioId, holdingId);
        setHoldings((prev) => prev.filter((h) => h.id !== holdingId));
        // Refresh summary after deleting holding
        refreshSummary();
        return true;
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to delete holding';
        setError(message);
        return false;
      } finally {
        setIsMutating(false);
      }
    },
    [portfolioId, refreshSummary]
  );

  const runRiskAnalysis = useCallback(async (): Promise<boolean> => {
    setIsGeneratingRiskAnalysis(true);
    setError(null);

    try {
      const result = await generateRiskAnalysis(portfolioId);
      setRiskAnalysis(result);
      return true;
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.detail : 'Failed to generate risk analysis';
      setError(message);
      return false;
    } finally {
      setIsGeneratingRiskAnalysis(false);
    }
  }, [portfolioId]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    portfolio,
    summary,
    holdings,
    riskAnalysis,
    isLoading,
    error,
    isMutating,
    isGeneratingRiskAnalysis,
    refetch,
    addHolding,
    editHolding,
    removeHolding,
    runRiskAnalysis,
    clearError,
  };
}
