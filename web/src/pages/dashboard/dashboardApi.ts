import { api } from '../../shared/api/client';
import type { PortfolioAnalytics } from '../../shared/types';

/**
 * Fetch portfolio analytics for the current session.
 */
export async function fetchAnalytics(sessionId: string): Promise<PortfolioAnalytics> {
  return api.get<PortfolioAnalytics>(`/analytics?session_id=${sessionId}`, sessionId);
}
