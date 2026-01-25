import { api } from '../../shared/api/client';
import type {
  SimulationCreateRequest,
  Simulation,
  SimulationSummary,
} from '../../shared/types/simulation';

/**
 * Create and run a new simulation
 */
export async function createSimulation(
  portfolioId: string,
  request: SimulationCreateRequest
): Promise<Simulation> {
  return api.post<Simulation>(
    `/portfolios/${portfolioId}/simulations`,
    request
  );
}

/**
 * List simulations for a portfolio
 */
export async function listSimulations(
  portfolioId: string
): Promise<SimulationSummary[]> {
  return api.get<SimulationSummary[]>(
    `/portfolios/${portfolioId}/simulations`
  );
}

/**
 * Get a single simulation with full results
 */
export async function getSimulation(
  simulationId: string
): Promise<Simulation> {
  return api.get<Simulation>(`/simulations/${simulationId}`);
}

/**
 * Delete a simulation
 */
export async function deleteSimulation(
  simulationId: string
): Promise<void> {
  return api.delete(`/simulations/${simulationId}`);
}

/**
 * Rename a simulation
 */
export async function renameSimulation(
  simulationId: string,
  name: string
): Promise<Simulation> {
  return api.patch<Simulation>(`/simulations/${simulationId}`, { name });
}
