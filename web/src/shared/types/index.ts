/**
 * Session represents a user session for the portfolio analytics application.
 * Sessions are used to group holdings together without requiring authentication.
 */
export interface Session {
  id: string;
  created_at: string;
  last_accessed_at: string;
}

/**
 * Holding represents a single investment holding in a portfolio.
 */
export interface Holding {
  id: string;
  session_id: string;
  ticker: string;
  name: string;
  asset_class: string;
  sector: string;
  broker: string;
  purchase_date: string;
  created_at: string;
}

/**
 * HoldingInput is the data required to create or update a holding.
 */
export interface HoldingInput {
  ticker: string;
  name: string;
  asset_class: string;
  sector: string;
  broker: string;
  purchase_date: string;
}

/**
 * TickerAnalytics contains performance metrics for a single holding.
 */
export interface TickerAnalytics {
  ticker: string;
  name: string;
  asset_class: string;
  sector: string;
  total_return_pct: number;
  annualized_return_pct: number;
  volatility_pct: number;
  sharpe_ratio: number;
  vs_benchmark_pct: number;
  expense_ratio: number | null;
}

/**
 * AssetClassBreakdown represents holdings aggregated by asset class.
 */
export interface AssetClassBreakdown {
  asset_class: string;
  count: number;
  avg_return: number;
}

/**
 * SectorBreakdown represents holdings aggregated by sector.
 */
export interface SectorBreakdown {
  sector: string;
  count: number;
  avg_return: number;
}

/**
 * PortfolioAnalytics contains aggregated analytics for the entire portfolio.
 */
export interface PortfolioAnalytics {
  holdings_count: number;
  avg_total_return_pct: number;
  avg_annualized_return_pct: number;
  avg_sharpe_ratio: number;
  beat_benchmark_count: number;
  holdings: TickerAnalytics[];
  asset_class_breakdown: AssetClassBreakdown[];
  sector_breakdown: SectorBreakdown[];
}

/**
 * API error response structure.
 */
export interface ApiError {
  detail: string;
  status: number;
}

/**
 * Available asset classes for holdings.
 */
export const ASSET_CLASSES = [
  'U.S. Stocks',
  'International Stocks',
  'Bonds',
  'Commodities',
  'Multi-Asset',
  'Cash & Equivalents',
] as const;

export type AssetClass = (typeof ASSET_CLASSES)[number];

/**
 * Available sectors for holdings.
 */
export const SECTORS = [
  'Financials',
  'Consumer Discretionary',
  'Healthcare',
  'Energy',
  'Materials',
  'Broad Market',
  'International',
  'Target Date',
  'Technology',
  'Money Market',
] as const;

export type Sector = (typeof SECTORS)[number];
