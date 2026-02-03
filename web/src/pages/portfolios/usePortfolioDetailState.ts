import { useState, useEffect, useCallback } from 'react';
import type {
  Portfolio,
  PortfolioSummary,
  Position,
  AddPositionInput,
  Transaction,
  RiskAnalysisResult,
  RiskAnalysisListItem,
} from '../../shared/types';
import { ApiClientError } from '../../shared/api/client';
import {
  getPortfolio,
  getPortfolioSummary,
  fetchPortfolioPositions,
  addPortfolioPosition,
  removePortfolioPosition,
  fetchPortfolioTransactions,
} from './portfolioApi';
import { useRiskAnalysisQueries } from './useRiskAnalysisQueries';

/**
 * State and operations for portfolio detail page.
 */
interface PortfolioDetailState {
  /** Portfolio data */
  portfolio: Portfolio | null;
  /** Portfolio summary */
  summary: PortfolioSummary | null;
  /** Portfolio positions */
  positions: Position[];
  /** Transaction history */
  transactions: Transaction[];
  /** Loading state for initial fetch */
  isLoading: boolean;
  /** Error message from last operation */
  error: string | null;
  /** Whether a mutation is in progress */
  isMutating: boolean;
  /** Refetch all data */
  refetch: () => Promise<void>;
  /** Add a new position */
  addPosition: (input: AddPositionInput) => Promise<boolean>;
  /** Remove a position */
  removePosition: (securityId: string) => Promise<boolean>;
  /** Clear current error */
  clearError: () => void;

  // Risk analysis state (from React Query)
  /** Current risk analysis result */
  riskAnalysis: RiskAnalysisResult | null;
  /** List of historical risk analyses */
  riskAnalysisList: RiskAnalysisListItem[];
  /** Whether risk analysis is being generated */
  isGeneratingRiskAnalysis: boolean;
  /** Whether switching between analyses */
  isLoadingAnalysis: boolean;
  /** Whether an analysis is being deleted */
  isDeletingAnalysis: boolean;
  /** Generate risk analysis */
  runRiskAnalysis: () => Promise<boolean>;
  /** Select a specific analysis from history */
  selectAnalysis: (analysisId: string | null) => void;
  /** Delete an analysis from history */
  removeAnalysis: (analysisId: string) => Promise<boolean>;
}

/**
 * Hook to manage portfolio detail state and operations.
 */
export function usePortfolioDetailState(portfolioId: string): PortfolioDetailState {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);

  // Risk analysis queries (managed by React Query)
  const {
    riskAnalysisList,
    riskAnalysis,
    isGeneratingRiskAnalysis,
    isLoadingAnalysis,
    isDeletingAnalysis,
    selectAnalysis,
    runRiskAnalysis,
    removeAnalysis,
  } = useRiskAnalysisQueries(portfolioId);

  const loadPortfolioData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch portfolio first to check access
      const portfolioData = await getPortfolio(portfolioId);
      setPortfolio(portfolioData);

      // Then fetch related data in parallel
      const [summaryData, positionsData, transactionsData] = await Promise.all([
        getPortfolioSummary(portfolioId).catch(() => null),
        fetchPortfolioPositions(portfolioId).catch(() => []),
        fetchPortfolioTransactions(portfolioId).catch(() => []),
      ]);

      setSummary(summaryData);
      setPositions(positionsData);
      setTransactions(transactionsData);
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

  const addPosition = useCallback(
    async (input: AddPositionInput): Promise<boolean> => {
      setIsMutating(true);
      setError(null);

      try {
        const newPosition = await addPortfolioPosition(portfolioId, input);
        setPositions((prev) => [...prev, newPosition]);
        // Refresh summary and transactions after adding position
        refreshSummary();
        fetchPortfolioTransactions(portfolioId)
          .then(setTransactions)
          .catch(() => {});
        return true;
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to add position';
        setError(message);
        return false;
      } finally {
        setIsMutating(false);
      }
    },
    [portfolioId, refreshSummary]
  );

  const removePosition = useCallback(
    async (securityId: string): Promise<boolean> => {
      setIsMutating(true);
      setError(null);

      try {
        await removePortfolioPosition(portfolioId, securityId);
        setPositions((prev) => prev.filter((p) => p.security_id !== securityId));
        // Refresh summary and transactions after removing position
        refreshSummary();
        fetchPortfolioTransactions(portfolioId)
          .then(setTransactions)
          .catch(() => {});
        return true;
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to remove position';
        setError(message);
        return false;
      } finally {
        setIsMutating(false);
      }
    },
    [portfolioId, refreshSummary]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    portfolio,
    summary,
    positions,
    transactions,
    isLoading,
    error,
    isMutating,
    refetch,
    addPosition,
    removePosition,
    clearError,

    // Risk analysis state (from React Query)
    riskAnalysis,
    riskAnalysisList,
    isGeneratingRiskAnalysis,
    isLoadingAnalysis,
    isDeletingAnalysis,
    runRiskAnalysis,
    selectAnalysis,
    removeAnalysis,
  };
}
