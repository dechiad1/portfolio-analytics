import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useEffect } from 'react';
import type { RiskAnalysisListItem } from '../../shared/types';
import {
  listRiskAnalyses,
  getRiskAnalysis,
  generateRiskAnalysis,
  deleteRiskAnalysis,
} from './portfolioApi';

/**
 * Query keys for risk analysis data.
 */
export const riskAnalysisKeys = {
  all: ['risk-analyses'] as const,
  list: (portfolioId: string) => ['risk-analyses', portfolioId] as const,
  detail: (portfolioId: string, analysisId: string) =>
    ['risk-analysis', portfolioId, analysisId] as const,
};

/**
 * Hook to manage risk analysis state and queries.
 */
export function useRiskAnalysisQueries(portfolioId: string) {
  const queryClient = useQueryClient();
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  // Track if selection was explicitly cleared to prevent auto-select race condition
  const [selectionCleared, setSelectionCleared] = useState(false);

  // Query: List all risk analyses
  const listQuery = useQuery({
    queryKey: riskAnalysisKeys.list(portfolioId),
    queryFn: () => listRiskAnalyses(portfolioId),
  });

  // Auto-select the first analysis when list loads (only if not explicitly cleared)
  useEffect(() => {
    if (listQuery.data && listQuery.data.length > 0 && !selectedAnalysisId && !selectionCleared) {
      setSelectedAnalysisId(listQuery.data[0].id);
    }
  }, [listQuery.data, selectedAnalysisId, selectionCleared]);

  // Query: Get selected analysis (enabled when an analysis is selected)
  const detailQuery = useQuery({
    queryKey: riskAnalysisKeys.detail(portfolioId, selectedAnalysisId ?? ''),
    queryFn: () => getRiskAnalysis(portfolioId, selectedAnalysisId!),
    enabled: !!selectedAnalysisId,
  });

  // Mutation: Generate new analysis
  const generateMutation = useMutation({
    mutationFn: () => generateRiskAnalysis(portfolioId),
    onSuccess: (newAnalysis) => {
      // Invalidate list to refetch
      queryClient.invalidateQueries({
        queryKey: riskAnalysisKeys.list(portfolioId),
      });
      // Set the new analysis in cache
      queryClient.setQueryData(
        riskAnalysisKeys.detail(portfolioId, newAnalysis.id),
        newAnalysis
      );
      // Select the new analysis and reset cleared flag
      setSelectedAnalysisId(newAnalysis.id);
      setSelectionCleared(false);
    },
  });

  // Mutation: Delete analysis
  const deleteMutation = useMutation({
    mutationFn: (analysisId: string) => deleteRiskAnalysis(portfolioId, analysisId),
    onSuccess: (_, deletedId) => {
      // Get current list before invalidation for auto-select logic
      const currentList = queryClient.getQueryData<RiskAnalysisListItem[]>(
        riskAnalysisKeys.list(portfolioId)
      );
      const remaining = currentList?.filter((a) => a.id !== deletedId) ?? [];

      // Invalidate list query
      queryClient.invalidateQueries({
        queryKey: riskAnalysisKeys.list(portfolioId),
      });

      // If we deleted the currently selected analysis, select the next one
      if (selectedAnalysisId === deletedId) {
        if (remaining.length > 0) {
          setSelectedAnalysisId(remaining[0].id);
          setSelectionCleared(false);
        } else {
          setSelectedAnalysisId(null);
          setSelectionCleared(true);
        }
      }

      // Remove the deleted analysis from cache
      queryClient.removeQueries({
        queryKey: riskAnalysisKeys.detail(portfolioId, deletedId),
      });
    },
  });

  const selectAnalysis = useCallback((analysisId: string | null) => {
    setSelectedAnalysisId(analysisId);
    // Reset cleared flag when explicitly selecting an analysis
    if (analysisId !== null) {
      setSelectionCleared(false);
    }
  }, []);

  // Generate wrapper that returns a boolean for compatibility
  const runRiskAnalysis = useCallback(async (): Promise<boolean> => {
    try {
      await generateMutation.mutateAsync();
      return true;
    } catch {
      return false;
    }
  }, [generateMutation]);

  // Delete wrapper
  const removeAnalysis = useCallback(
    async (analysisId: string): Promise<boolean> => {
      try {
        await deleteMutation.mutateAsync(analysisId);
        return true;
      } catch {
        return false;
      }
    },
    [deleteMutation]
  );

  return {
    // List data
    riskAnalysisList: listQuery.data ?? [],
    isLoadingList: listQuery.isLoading,
    listError: listQuery.error,

    // Selected analysis data
    selectedAnalysisId,
    riskAnalysis: detailQuery.data ?? null,
    isLoadingAnalysis: detailQuery.isLoading,
    analysisError: detailQuery.error,

    // Mutations
    isGeneratingRiskAnalysis: generateMutation.isPending,
    generateError: generateMutation.error,
    isDeletingAnalysis: deleteMutation.isPending,

    // Actions
    selectAnalysis,
    runRiskAnalysis,
    removeAnalysis,
  };
}
