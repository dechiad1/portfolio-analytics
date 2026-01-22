import type { PortfolioSummary } from '../../../shared/types';
import styles from './SummaryCards.module.css';

interface SummaryCardsProps {
  summary: PortfolioSummary;
}

/**
 * Format a number as currency.
 */
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

/**
 * Format a number as a percentage.
 */
function formatPercentage(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
}

/**
 * SummaryCards displays key portfolio metrics.
 */
export function SummaryCards({ summary }: SummaryCardsProps) {
  const isPositive = summary.total_gain_loss >= 0;

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
            <line x1="12" y1="1" x2="12" y2="23" />
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <div className={styles.cardContent}>
          <p className={styles.cardLabel}>Total Value</p>
          <p className={styles.cardValue}>{formatCurrency(summary.total_value)}</p>
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
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
            <line x1="1" y1="10" x2="23" y2="10" />
          </svg>
        </div>
        <div className={styles.cardContent}>
          <p className={styles.cardLabel}>Total Cost</p>
          <p className={styles.cardValue}>{formatCurrency(summary.total_cost)}</p>
        </div>
      </div>

      <div className={styles.card}>
        <div className={`${styles.cardIcon} ${isPositive ? styles.iconPositive : styles.iconNegative}`}>
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
            {isPositive ? (
              <>
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                <polyline points="17 6 23 6 23 12" />
              </>
            ) : (
              <>
                <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
                <polyline points="17 18 23 18 23 12" />
              </>
            )}
          </svg>
        </div>
        <div className={styles.cardContent}>
          <p className={styles.cardLabel}>Total Gain/Loss</p>
          <p className={`${styles.cardValue} ${isPositive ? styles.valuePositive : styles.valueNegative}`}>
            {formatCurrency(summary.total_gain_loss)}
            <span className={styles.percentage}>
              ({formatPercentage(summary.total_gain_loss_percentage)})
            </span>
          </p>
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
            <line x1="8" y1="6" x2="21" y2="6" />
            <line x1="8" y1="12" x2="21" y2="12" />
            <line x1="8" y1="18" x2="21" y2="18" />
            <line x1="3" y1="6" x2="3.01" y2="6" />
            <line x1="3" y1="12" x2="3.01" y2="12" />
            <line x1="3" y1="18" x2="3.01" y2="18" />
          </svg>
        </div>
        <div className={styles.cardContent}>
          <p className={styles.cardLabel}>Holdings</p>
          <p className={styles.cardValue}>{summary.holdings_count}</p>
        </div>
      </div>
    </div>
  );
}
