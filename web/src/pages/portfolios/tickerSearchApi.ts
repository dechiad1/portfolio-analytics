import { api } from '../../shared/api/client';

export interface TickerSearchResult {
  ticker: string;
  name: string;
  asset_class: string;
  category: string | null;
}

export interface TickerDetails {
  ticker: string;
  name: string;
  asset_class: string;
  sector: string | null;
  category: string | null;
  latest_price: number | null;
  latest_price_date: string | null;
}

export interface TickerPrice {
  ticker: string;
  price_date: string;
  price: number;
}

interface TickerSearchResponse {
  results: TickerSearchResult[];
  count: number;
}

/**
 * Search for tickers by symbol or name.
 */
export async function searchTickers(query: string, limit: number = 20): Promise<TickerSearchResult[]> {
  if (!query || query.trim().length === 0) {
    return [];
  }

  const response = await api.get<TickerSearchResponse>(
    `/analytics/tickers/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );

  return response.results;
}

/**
 * Get detailed ticker info including latest price.
 */
export async function getTickerDetails(ticker: string): Promise<TickerDetails> {
  return api.get<TickerDetails>(`/analytics/tickers/${encodeURIComponent(ticker)}/details`);
}

/**
 * Get price for a ticker at a specific date.
 */
export async function getTickerPrice(ticker: string, date: string): Promise<TickerPrice> {
  return api.get<TickerPrice>(`/analytics/tickers/${encodeURIComponent(ticker)}/price?date=${date}`);
}
