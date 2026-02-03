import { api } from '../../shared/api/client';
import type {
  Portfolio,
  PortfolioWithUser,
  PortfolioInput,
  PortfolioSummary,
  RiskAnalysisResult,
  RiskAnalysisListItem,
  CreatePortfolioResult,
  Position,
  AddPositionInput,
  Transaction,
} from '../../shared/types';

/**
 * Fetch all portfolios for the current user.
 */
export async function fetchPortfolios(): Promise<Portfolio[]> {
  const response = await api.get<{ portfolios: Portfolio[] }>('/portfolios');
  return response.portfolios;
}

/**
 * Fetch all portfolios with user info.
 */
export async function fetchAllPortfolios(): Promise<PortfolioWithUser[]> {
  const response = await api.get<{ portfolios: PortfolioWithUser[] }>('/portfolios/all');
  return response.portfolios;
}

/**
 * Create a new portfolio.
 */
export async function createPortfolio(input: PortfolioInput): Promise<CreatePortfolioResult> {
  return api.post<CreatePortfolioResult>('/portfolios', input);
}

/**
 * Get a portfolio by ID.
 */
export async function getPortfolio(portfolioId: string): Promise<Portfolio> {
  return api.get<Portfolio>(`/portfolios/${portfolioId}`);
}

/**
 * Update a portfolio.
 */
export async function updatePortfolio(
  portfolioId: string,
  input: PortfolioInput
): Promise<Portfolio> {
  return api.put<Portfolio>(`/portfolios/${portfolioId}`, input);
}

/**
 * Delete a portfolio.
 */
export async function deletePortfolio(portfolioId: string): Promise<void> {
  return api.delete(`/portfolios/${portfolioId}`);
}

/**
 * Get portfolio summary with breakdowns.
 */
export async function getPortfolioSummary(portfolioId: string): Promise<PortfolioSummary> {
  return api.get<PortfolioSummary>(`/portfolios/${portfolioId}/summary`);
}

/**
 * Generate AI risk analysis for a portfolio.
 */
export async function generateRiskAnalysis(portfolioId: string): Promise<RiskAnalysisResult> {
  return api.post<RiskAnalysisResult>(`/portfolios/${portfolioId}/risk-analysis`);
}

/**
 * List all risk analyses for a portfolio.
 */
export async function listRiskAnalyses(portfolioId: string): Promise<RiskAnalysisListItem[]> {
  const response = await api.get<{ analyses: RiskAnalysisListItem[] }>(
    `/portfolios/${portfolioId}/risk-analyses`
  );
  return response.analyses;
}

/**
 * Get a specific risk analysis by ID.
 */
export async function getRiskAnalysis(
  portfolioId: string,
  analysisId: string
): Promise<RiskAnalysisResult> {
  return api.get<RiskAnalysisResult>(
    `/portfolios/${portfolioId}/risk-analyses/${analysisId}`
  );
}

/**
 * Delete a risk analysis.
 */
export async function deleteRiskAnalysis(
  portfolioId: string,
  analysisId: string
): Promise<void> {
  return api.delete(`/portfolios/${portfolioId}/risk-analyses/${analysisId}`);
}

// Position-centric API (new)

/**
 * Fetch all positions for a portfolio.
 */
export async function fetchPortfolioPositions(portfolioId: string): Promise<Position[]> {
  const response = await api.get<{ positions: Position[]; count: number }>(
    `/portfolios/${portfolioId}/positions`
  );
  return response.positions;
}

/**
 * Add a position to a portfolio (creates a BUY transaction).
 */
export async function addPortfolioPosition(
  portfolioId: string,
  input: AddPositionInput
): Promise<Position> {
  return api.post<Position>(`/portfolios/${portfolioId}/positions`, input);
}

/**
 * Remove a position from a portfolio (creates a SELL transaction for full quantity).
 */
export async function removePortfolioPosition(
  portfolioId: string,
  securityId: string
): Promise<void> {
  return api.delete(`/portfolios/${portfolioId}/positions/${securityId}`);
}

/**
 * Fetch all transactions for a portfolio.
 */
export async function fetchPortfolioTransactions(portfolioId: string): Promise<Transaction[]> {
  const response = await api.get<{ transactions: Transaction[]; count: number }>(
    `/portfolios/${portfolioId}/transactions`
  );
  return response.transactions;
}
