import { useState, useEffect, useCallback } from 'react';
import type { Simulation } from '../../shared/types/simulation';
import { getSimulation, deleteSimulation } from '../portfolios/simulationApi';
import { ApiClientError } from '../../shared/api/client';

interface SimulationDetailState {
  simulation: Simulation | null;
  isLoading: boolean;
  error: string | null;
  isDeleting: boolean;
}

interface SimulationDetailActions {
  handleDelete: () => Promise<boolean>;
}

export function useSimulationDetailState(
  simulationId: string | undefined
): SimulationDetailState & SimulationDetailActions {
  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (!simulationId) {
      setIsLoading(false);
      setError('No simulation ID provided');
      return;
    }

    async function loadSimulation() {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getSimulation(simulationId!);
        setSimulation(data);
      } catch (err) {
        if (err instanceof ApiClientError) {
          setError(err.detail);
        } else {
          setError('Failed to load simulation');
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadSimulation();
  }, [simulationId]);

  const handleDelete = useCallback(async (): Promise<boolean> => {
    if (!simulationId) return false;

    try {
      setIsDeleting(true);
      await deleteSimulation(simulationId);
      return true;
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError('Failed to delete simulation');
      }
      return false;
    } finally {
      setIsDeleting(false);
    }
  }, [simulationId]);

  return {
    simulation,
    isLoading,
    error,
    isDeleting,
    handleDelete,
  };
}
