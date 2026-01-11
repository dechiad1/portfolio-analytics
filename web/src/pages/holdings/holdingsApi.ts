import { api } from '../../shared/api/client';
import type { Holding, HoldingInput } from '../../shared/types';

/**
 * Fetch all holdings.
 */
export async function fetchHoldings(): Promise<Holding[]> {
  const response = await api.get<{ holdings: Holding[] }>('/holdings');
  return response.holdings;
}

/**
 * Create a new holding.
 */
export async function createHolding(holding: HoldingInput): Promise<Holding> {
  return api.post<Holding>('/holdings', holding);
}

/**
 * Update an existing holding.
 */
export async function updateHolding(
  holdingId: string,
  holding: HoldingInput
): Promise<Holding> {
  return api.put<Holding>(`/holdings/${holdingId}`, holding);
}

/**
 * Delete a holding.
 */
export async function deleteHolding(holdingId: string): Promise<void> {
  return api.delete(`/holdings/${holdingId}`);
}

/**
 * Upload a CSV file of holdings.
 */
export async function uploadHoldingsCsv(file: File): Promise<Holding[]> {
  const response = await api.upload<{ holdings: Holding[] }>('/holdings/upload', file, 'file');
  return response.holdings;
}
