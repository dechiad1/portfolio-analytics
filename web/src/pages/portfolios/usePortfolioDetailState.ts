import { useState, useEffect, useCallback } from 'react';
import type {
  Portfolio,
  PortfolioSummary,
  PortfolioHolding,
  PortfolioHoldingInput,
  RiskAnalysisResult,
  RiskAnalysisListItem,
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
  listRiskAnalyses,
  getRiskAnalysis,
  deleteRiskAnalysis,
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
  /** Current risk analysis result */
  riskAnalysis: RiskAnalysisResult | null;
  /** List of historical risk analyses */
  riskAnalysisList: RiskAnalysisListItem[];
  /** Loading state for initial fetch */
  isLoading: boolean;
  /** Error message from last operation */
  error: string | null;
  /** Whether a mutation is in progress */
  isMutating: boolean;
  /** Whether risk analysis is being generated */
  isGeneratingRiskAnalysis: boolean;
  /** Whether switching between analyses */
  isLoadingAnalysis: boolean;
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
  /** Select a specific analysis from history */
  selectAnalysis: (analysisId: string) => Promise<boolean>;
  /** Delete an analysis from history */
  removeAnalysis: (analysisId: string) => Promise<boolean>;
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
  const [riskAnalysisList, setRiskAnalysisList] = useState<RiskAnalysisListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [isGeneratingRiskAnalysis, setIsGeneratingRiskAnalysis] = useState(false);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);

  const loadPortfolioData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch portfolio first to check access
      const portfolioData = await getPortfolio(portfolioId);
      setPortfolio(portfolioData);

      // Then fetch related data in parallel
      const [summaryData, holdingsData, analysesData] = await Promise.all([
        getPortfolioSummary(portfolioId).catch(() => null),
        fetchPortfolioHoldings(portfolioId).catch(() => []),
        listRiskAnalyses(portfolioId).catch(() => []),
      ]);

      setSummary(summaryData);
      setHoldings(holdingsData);
      setRiskAnalysisList(analysesData);

      // Load the latest analysis if available
      if (analysesData.length > 0) {
        try {
          const latestAnalysis = await getRiskAnalysis(portfolioId, analysesData[0].id);
          setRiskAnalysis(latestAnalysis);
        } catch {
          // Silently fail - analysis data is not critical
        }
      }
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
      // Add to list at the beginning (most recent first)
      setRiskAnalysisList((prev) => [
        {
          id: result.id,
          created_at: result.created_at,
          model_used: result.model_used,
          risk_count: result.risks.length,
        },
        ...prev,
      ]);
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

  const selectAnalysis = useCallback(
    async (analysisId: string): Promise<boolean> => {
      // Check if already selected
      if (riskAnalysis?.id === analysisId) {
        return true;
      }

      setIsLoadingAnalysis(true);
      setError(null);

      try {
        const result = await getRiskAnalysis(portfolioId, analysisId);
        setRiskAnalysis(result);
        return true;
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to load risk analysis';
        setError(message);
        return false;
      } finally {
        setIsLoadingAnalysis(false);
      }
    },
    [portfolioId, riskAnalysis?.id]
  );

  const removeAnalysis = useCallback(
    async (analysisId: string): Promise<boolean> => {
      setIsMutating(true);
      setError(null);

      try {
        await deleteRiskAnalysis(portfolioId, analysisId);
        setRiskAnalysisList((prev) => prev.filter((a) => a.id !== analysisId));
        // Clear current analysis if it was deleted
        if (riskAnalysis?.id === analysisId) {
          setRiskAnalysis(null);
        }
        return true;
      } catch (err) {
        const message =
          err instanceof ApiClientError ? err.detail : 'Failed to delete risk analysis';
        setError(message);
        return false;
      } finally {
        setIsMutating(false);
      }
    },
    [portfolioId, riskAnalysis?.id]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    portfolio,
    summary,
    holdings,
    riskAnalysis,
    riskAnalysisList,
    isLoading,
    error,
    isMutating,
    isGeneratingRiskAnalysis,
    isLoadingAnalysis,
    refetch,
    addHolding,
    editHolding,
    removeHolding,
    runRiskAnalysis,
    selectAnalysis,
    removeAnalysis,
    clearError,
  };
}
