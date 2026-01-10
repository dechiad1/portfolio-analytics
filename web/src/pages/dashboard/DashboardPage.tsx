import { Link } from 'react-router-dom';
import { LoadingSpinner } from '../../shared/components/LoadingSpinner';
import { ErrorMessage } from '../../shared/components/ErrorMessage';
import { useDashboardData } from './useDashboardData';
import { MetricsCards } from './components/MetricsCards';
import { RiskReturnChart } from './components/RiskReturnChart';
import { AssetAllocationChart } from './components/AssetAllocationChart';
import { BenchmarkComparison } from './components/BenchmarkComparison';
import styles from './DashboardPage.module.css';

/**
 * DashboardPage displays portfolio analytics and charts.
 */
export function DashboardPage() {
  const { analytics, isLoading, error, refetch } = useDashboardData();

  if (isLoading) {
    return (
      <div className={styles.page}>
        <LoadingSpinner size="large" message="Loading analytics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <ErrorMessage message={error} onRetry={refetch} />
      </div>
    );
  }

  // Empty state - no holdings
  if (!analytics || analytics.holdings_count === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <svg
            className={styles.emptyIcon}
            xmlns="http://www.w3.org/2000/svg"
            width="64"
            height="64"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="12" y1="20" x2="12" y2="10" />
            <line x1="18" y1="20" x2="18" y2="4" />
            <line x1="6" y1="20" x2="6" y2="16" />
          </svg>
          <h2 className={styles.emptyTitle}>No Holdings Yet</h2>
          <p className={styles.emptyText}>
            Add some holdings to see your portfolio analytics and performance metrics.
          </p>
          <Link to="/holdings" className={styles.emptyButton}>
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
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add Holdings
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Dashboard</h1>
        <p className={styles.subtitle}>
          Portfolio overview with {analytics.holdings_count} holding
          {analytics.holdings_count !== 1 ? 's' : ''}
        </p>
      </div>

      <section className={styles.section}>
        <MetricsCards analytics={analytics} />
      </section>

      <section className={styles.section}>
        <RiskReturnChart holdings={analytics.holdings} />
      </section>

      <section className={styles.section}>
        <AssetAllocationChart
          assetClassBreakdown={analytics.asset_class_breakdown}
          sectorBreakdown={analytics.sector_breakdown}
        />
      </section>

      <section className={styles.section}>
        <BenchmarkComparison holdings={analytics.holdings} />
      </section>
    </div>
  );
}
