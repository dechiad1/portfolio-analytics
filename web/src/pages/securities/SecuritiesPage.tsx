import { useState } from 'react';
import { LoadingSpinner } from '../../shared/components/LoadingSpinner';
import { ErrorMessage } from '../../shared/components/ErrorMessage';
import { useSecuritiesState } from './useSecuritiesState';
import { SecuritiesTable } from './components/SecuritiesTable';
import { AddTickerModal } from './components/AddTickerModal';
import { PendingTickersBanner } from './components/PendingTickersBanner';
import { addTicker } from './securitiesApi';
import styles from './SecuritiesPage.module.css';

type TimePeriod = '1Y' | '5Y';

/**
 * SecuritiesPage displays all available securities from DuckDB.
 */
export function SecuritiesPage() {
  const { securities, userAddedTickers, isLoading, error, refetch, clearError } = useSecuritiesState();
  const [period, setPeriod] = useState<TimePeriod>('1Y');
  const [showAddTickerModal, setShowAddTickerModal] = useState(false);

  if (isLoading) {
    return (
      <div className={styles.page}>
        <LoadingSpinner size="large" message="Loading securities..." />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Securities</h1>
          <p className={styles.subtitle}>
            Browse all available securities and their performance metrics.
          </p>
        </div>
        <div className={styles.headerRight}>
          <button
            className={styles.trackButton}
            onClick={() => setShowAddTickerModal(true)}
          >
            + Track Ticker
          </button>
          <div className={styles.periodToggle}>
            <button
              className={`${styles.periodButton} ${period === '1Y' ? styles.periodButtonActive : ''}`}
              onClick={() => setPeriod('1Y')}
            >
              1Y
            </button>
            <button
              className={`${styles.periodButton} ${period === '5Y' ? styles.periodButtonActive : ''}`}
              onClick={() => setPeriod('5Y')}
            >
              5Y
            </button>
          </div>
          <div className={styles.stats}>
            <span className={styles.count}>{securities.length} securities</span>
          </div>
        </div>
      </div>

      {error && (
        <div className={styles.errorContainer}>
          <ErrorMessage
            message={error}
            onRetry={() => {
              clearError();
              refetch();
            }}
          />
        </div>
      )}

      <PendingTickersBanner
        userAddedTickers={userAddedTickers}
        securities={securities}
      />

      {securities.length === 0 ? (
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
            <line x1="8" y1="6" x2="21" y2="6" />
            <line x1="8" y1="12" x2="21" y2="12" />
            <line x1="8" y1="18" x2="21" y2="18" />
            <line x1="3" y1="6" x2="3.01" y2="6" />
            <line x1="3" y1="12" x2="3.01" y2="12" />
            <line x1="3" y1="18" x2="3.01" y2="18" />
          </svg>
          <h2 className={styles.emptyTitle}>No Securities Found</h2>
          <p className={styles.emptyText}>
            No securities are currently available in the database.
          </p>
        </div>
      ) : (
        <SecuritiesTable securities={securities} period={period} />
      )}

      {showAddTickerModal && (
        <AddTickerModal
          onSubmit={addTicker}
          onClose={() => setShowAddTickerModal(false)}
          onSuccess={refetch}
        />
      )}
    </div>
  );
}
