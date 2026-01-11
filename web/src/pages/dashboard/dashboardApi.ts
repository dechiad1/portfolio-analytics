import { api } from '../../shared/api/client';
import type { PortfolioAnalytics } from '../../shared/types';

/**
 * Fetch portfolio analytics for all holdings.
 */
export async function fetchAnalytics(): Promise<PortfolioAnalytics> {
  return api.get<PortfolioAnalytics>('/analytics');
}
