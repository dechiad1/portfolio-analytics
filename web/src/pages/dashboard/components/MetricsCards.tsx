import type { PortfolioAnalytics } from '../../../shared/types';
import styles from './MetricsCards.module.css';

interface MetricsCardsProps {
  analytics: PortfolioAnalytics;
}

/**
 * Format a percentage value for display.
 */
function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Get the best performing holding from the analytics.
 */
function getBestPerformer(analytics: PortfolioAnalytics): { ticker: string; return: number } | null {
  if (analytics.holdings.length === 0) return null;

  const best = analytics.holdings.reduce((prev, current) =>
    current.total_return_pct > prev.total_return_pct ? current : prev
  );

  return { ticker: best.ticker, return: best.total_return_pct };
}

/**
 * MetricsCards displays key portfolio metrics in a card layout.
 */
export function MetricsCards({ analytics }: MetricsCardsProps) {
  const bestPerformer = getBestPerformer(analytics);

  return (
    <div className={styles.grid}>
      <div className={styles.card}>
        <div className={styles.cardIcon}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
        </div>
        <div className={styles.cardContent}>
          <span className={styles.cardLabel}>Avg Total Return</span>
          <span
            className={`${styles.cardValue} ${
              analytics.avg_total_return_pct >= 0 ? styles.positive : styles.negative
            }`}
          >
            {formatPercent(analytics.avg_total_return_pct)}
          </span>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardIcon}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        </div>
        <div className={styles.cardContent}>
          <span className={styles.cardLabel}>Best Performer</span>
          {bestPerformer ? (
            <div className={styles.bestPerformer}>
              <span className={styles.ticker}>{bestPerformer.ticker}</span>
              <span
                className={`${styles.returnValue} ${
                  bestPerformer.return >= 0 ? styles.positive : styles.negative
                }`}
              >
                {formatPercent(bestPerformer.return)}
              </span>
            </div>
          ) : (
            <span className={styles.cardValue}>--</span>
          )}
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardIcon}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="12" y1="1" x2="12" y2="23" />
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <div className={styles.cardContent}>
          <span className={styles.cardLabel}>Avg Sharpe Ratio</span>
          <span className={styles.cardValue}>
            {analytics.avg_sharpe_ratio.toFixed(2)}
          </span>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardIcon}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        </div>
        <div className={styles.cardContent}>
          <span className={styles.cardLabel}>Beat S&P 500</span>
          <span className={styles.cardValue}>
            {analytics.beat_benchmark_count} / {analytics.holdings_count}
          </span>
        </div>
      </div>
    </div>
  );
}
