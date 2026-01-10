import { api } from '../../shared/api/client';
import type { Holding, HoldingInput } from '../../shared/types';

/**
 * Fetch all holdings for the current session.
 */
export async function fetchHoldings(sessionId: string): Promise<Holding[]> {
  return api.get<Holding[]>(`/holdings?session_id=${sessionId}`, sessionId);
}

/**
 * Create a new holding.
 */
export async function createHolding(
  sessionId: string,
  holding: HoldingInput
): Promise<Holding> {
  return api.post<Holding>('/holdings', holding, sessionId);
}

/**
 * Update an existing holding.
 */
export async function updateHolding(
  sessionId: string,
  holdingId: string,
  holding: HoldingInput
): Promise<Holding> {
  return api.put<Holding>(`/holdings/${holdingId}`, holding, sessionId);
}

/**
 * Delete a holding.
 */
export async function deleteHolding(
  sessionId: string,
  holdingId: string
): Promise<void> {
  return api.delete(`/holdings/${holdingId}`, sessionId);
}

/**
 * Upload a CSV file of holdings.
 */
export async function uploadHoldingsCsv(
  sessionId: string,
  file: File
): Promise<Holding[]> {
  return api.upload<Holding[]>('/holdings/upload', file, 'file', sessionId);
}
