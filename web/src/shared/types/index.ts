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

/**
 * User represents an authenticated user.
 */
export interface User {
  id: string;
  email: string;
  created_at: string;
}

/**
 * AuthTokens returned from login/register.
 */
export interface AuthTokens {
  access_token: string;
  token_type: string;
}

/**
 * Login credentials.
 */
export interface LoginCredentials {
  email: string;
  password: string;
}

/**
 * Registration credentials.
 */
export interface RegisterCredentials {
  email: string;
  password: string;
}

/**
 * Portfolio represents a user's investment portfolio.
 */
export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * PortfolioWithUser represents a portfolio with owner email.
 */
export interface PortfolioWithUser {
  id: string;
  user_id: string;
  user_email: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * PortfolioInput is the data required to create or update a portfolio.
 */
export interface PortfolioInput {
  name: string;
  description?: string;
}

/**
 * PortfolioHolding represents a single holding within a portfolio.
 */
export interface PortfolioHolding {
  id: string;
  portfolio_id: string;
  ticker: string;
  name: string;
  asset_type: string;
  asset_class: string;
  sector: string;
  broker: string;
  quantity: number;
  purchase_price: number;
  current_price: number;
  purchase_date: string;
  created_at: string;
  updated_at: string;
}

/**
 * PortfolioHoldingInput is the data required to create or update a portfolio holding.
 */
export interface PortfolioHoldingInput {
  ticker: string;
  name: string;
  asset_type: string;
  asset_class: string;
  sector: string;
  broker: string;
  quantity: number;
  purchase_price: number;
  current_price: number;
  purchase_date: string;
}

/**
 * BreakdownItem represents a single item in portfolio breakdowns.
 */
export interface BreakdownItem {
  name: string;
  value: number;
  percentage: number;
}

/**
 * PortfolioSummary contains aggregated portfolio data.
 */
export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_gain_loss: number;
  total_gain_loss_percentage: number;
  holdings_count: number;
  by_asset_type: BreakdownItem[];
  by_asset_class: BreakdownItem[];
  by_sector: BreakdownItem[];
}

/**
 * RiskAnalysisResult contains AI-generated risk analysis.
 */
export interface RiskAnalysisResult {
  analysis: string;
  generated_at: string;
}

/**
 * Available asset types for holdings (display values).
 */
export const ASSET_TYPES = [
  'Stock',
  'ETF',
  'Mutual Fund',
  'Bond',
  'REIT',
  'Cryptocurrency',
  'Commodity',
  'Cash',
] as const;

export type AssetType = (typeof ASSET_TYPES)[number];

/**
 * Mapping from display asset type to API value.
 */
export const ASSET_TYPE_TO_API: Record<AssetType, string> = {
  'Stock': 'equity',
  'ETF': 'etf',
  'Mutual Fund': 'mutual_fund',
  'Bond': 'bond',
  'REIT': 'equity',
  'Cryptocurrency': 'equity',
  'Commodity': 'equity',
  'Cash': 'cash',
};

/**
 * Mapping from API asset type to display value.
 */
export const API_TO_ASSET_TYPE: Record<string, AssetType> = {
  'equity': 'Stock',
  'etf': 'ETF',
  'mutual_fund': 'Mutual Fund',
  'bond': 'Bond',
  'cash': 'Cash',
};
