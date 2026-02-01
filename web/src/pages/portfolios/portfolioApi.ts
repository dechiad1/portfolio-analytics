import { api } from '../../shared/api/client';
import type {
  Portfolio,
  PortfolioWithUser,
  PortfolioInput,
  PortfolioHolding,
  PortfolioHoldingInput,
  PortfolioSummary,
  RiskAnalysisResult,
  RiskAnalysisListItem,
  CreatePortfolioResult,
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
 * Fetch all holdings for a portfolio.
 */
export async function fetchPortfolioHoldings(portfolioId: string): Promise<PortfolioHolding[]> {
  const response = await api.get<{ holdings: PortfolioHolding[] }>(
    `/portfolios/${portfolioId}/holdings`
  );
  return response.holdings;
}

/**
 * Add a holding to a portfolio.
 */
export async function addPortfolioHolding(
  portfolioId: string,
  input: PortfolioHoldingInput
): Promise<PortfolioHolding> {
  return api.post<PortfolioHolding>(`/portfolios/${portfolioId}/holdings`, input);
}

/**
 * Update a holding in a portfolio.
 */
export async function updatePortfolioHolding(
  portfolioId: string,
  holdingId: string,
  input: PortfolioHoldingInput
): Promise<PortfolioHolding> {
  return api.put<PortfolioHolding>(
    `/portfolios/${portfolioId}/holdings/${holdingId}`,
    input
  );
}

/**
 * Delete a holding from a portfolio.
 */
export async function deletePortfolioHolding(
  portfolioId: string,
  holdingId: string
): Promise<void> {
  return api.delete(`/portfolios/${portfolioId}/holdings/${holdingId}`);
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
