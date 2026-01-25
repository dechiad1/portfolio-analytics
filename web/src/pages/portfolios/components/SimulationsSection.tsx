import { useState, useEffect, useCallback } from 'react';
import type { SimulationSummary, SimulationCreateRequest } from '../../../shared/types/simulation';
import { DEFAULT_SIMULATION_CONFIG } from '../../../shared/types/simulation';
import { listSimulations, createSimulation, deleteSimulation } from '../simulationApi';
import { SimulationCard } from './SimulationCard';
import { SimulationConfigModal } from './SimulationConfigModal';
import { ApiClientError } from '../../../shared/api/client';
import styles from './SimulationsSection.module.css';

interface SimulationsSectionProps {
  portfolioId: string;
  hasHoldings: boolean;
}

/**
 * SimulationsSection displays simulation cards and controls.
 */
export function SimulationsSection({
  portfolioId,
  hasHoldings,
}: SimulationsSectionProps) {
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadSimulations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await listSimulations(portfolioId);
      setSimulations(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError('Failed to load simulations');
      }
    } finally {
      setIsLoading(false);
    }
  }, [portfolioId]);

  useEffect(() => {
    loadSimulations();
  }, [loadSimulations]);

  const handleRunSimulation = async (config: SimulationCreateRequest) => {
    try {
      setIsRunning(true);
      setError(null);
      await createSimulation(portfolioId, config);
      await loadSimulations();
      setIsModalOpen(false);
    } catch (err) {
      if (err instanceof ApiClientError) {
        throw new Error(err.detail);
      }
      throw new Error('Failed to run simulation');
    } finally {
      setIsRunning(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      setDeletingId(id);
      await deleteSimulation(id);
      setSimulations((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError('Failed to delete simulation');
      }
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h2 className={styles.title}>Simulations</h2>
          <p className={styles.description}>
            Run Monte Carlo simulations to stress test your portfolio
          </p>
        </div>
        <button
          className={styles.newButton}
          onClick={() => setIsModalOpen(true)}
          disabled={!hasHoldings}
          title={!hasHoldings ? 'Add holdings to run simulations' : 'Run new simulation'}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Simulation
        </button>
      </div>

      {error && (
        <div className={styles.error}>
          <p>{error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {isLoading && (
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>Loading simulations...</p>
        </div>
      )}

      {!isLoading && !hasHoldings && (
        <div className={styles.emptyState}>
          <svg
            className={styles.emptyIcon}
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <p className={styles.emptyText}>
            Add holdings to your portfolio to run simulations.
          </p>
        </div>
      )}

      {!isLoading && hasHoldings && simulations.length === 0 && (
        <div className={styles.emptyState}>
          <svg
            className={styles.emptyIcon}
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
          <p className={styles.emptyText}>
            No simulations yet. Click "New Simulation" to stress test your portfolio.
          </p>
        </div>
      )}

      {!isLoading && simulations.length > 0 && (
        <div className={styles.grid}>
          {simulations.map((sim) => (
            <SimulationCard
              key={sim.id}
              simulation={sim}
              onDelete={handleDelete}
              isDeleting={deletingId === sim.id}
            />
          ))}
        </div>
      )}

      {isModalOpen && (
        <SimulationConfigModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleRunSimulation}
          isRunning={isRunning}
          defaultConfig={DEFAULT_SIMULATION_CONFIG}
        />
      )}
    </div>
  );
}
