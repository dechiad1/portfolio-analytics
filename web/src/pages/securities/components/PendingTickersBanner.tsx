import type { UserAddedTicker, Security } from '../securitiesApi';
import styles from './PendingTickersBanner.module.css';

interface PendingTickersBannerProps {
  userAddedTickers: UserAddedTicker[];
  securities: Security[];
}

/**
 * Displays a warning banner for tickers that have been added but don't have data yet.
 * Compares user-added tickers (from PostgreSQL) with securities (from DuckDB mart).
 */
export function PendingTickersBanner({
  userAddedTickers,
  securities,
}: PendingTickersBannerProps) {
  // Get set of tickers that have data in the mart
  const securitiesWithData = new Set(
    securities.map((s) => s.ticker.toUpperCase())
  );

  // Find user-added tickers that don't have data yet
  const pendingTickers = userAddedTickers.filter(
    (t) => !securitiesWithData.has(t.ticker.toUpperCase())
  );

  if (pendingTickers.length === 0) {
    return null;
  }

  return (
    <div className={styles.banner}>
      <div className={styles.iconContainer}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <div className={styles.content}>
        <p className={styles.title}>
          {pendingTickers.length === 1
            ? '1 ticker pending data refresh'
            : `${pendingTickers.length} tickers pending data refresh`}
        </p>
        <p className={styles.description}>
          The following tickers have been added but don't have performance data yet:{' '}
          <span className={styles.tickers}>
            {pendingTickers.map((t) => t.ticker).join(', ')}
          </span>
        </p>
        <p className={styles.hint}>
          Run <code>task refresh</code> to fetch historical data for these tickers.
        </p>
      </div>
    </div>
  );
}
