import { api } from '../../shared/api/client';

export interface TickerSearchResult {
  ticker: string;
  name: string;
  asset_class: string;
  category: string | null;
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
