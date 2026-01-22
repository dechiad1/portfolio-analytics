import { api } from '../../shared/api/client';

export interface Security {
  ticker: string;
  name: string;
  asset_class: string;
  category: string | null;
  expense_ratio: number | null;
  // 1-Year metrics
  total_return_1y_pct: number | null;
  return_vs_risk_free_1y_pct: number | null;
  return_vs_sp500_1y_pct: number | null;
  volatility_1y_pct: number | null;
  sharpe_ratio_1y: number | null;
  // 5-Year metrics
  total_return_5y_pct: number | null;
  return_vs_risk_free_5y_pct: number | null;
  return_vs_sp500_5y_pct: number | null;
  volatility_5y_pct: number | null;
  sharpe_ratio_5y: number | null;
}

interface SecuritiesListResponse {
  securities: Security[];
  count: number;
}

/**
 * Fetch all available securities.
 */
export async function fetchSecurities(): Promise<Security[]> {
  const response = await api.get<SecuritiesListResponse>('/analytics/securities');
  return response.securities;
}
