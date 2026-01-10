import type { Holding } from '../../../shared/types';
import styles from './HoldingsTable.module.css';

interface HoldingsTableProps {
  /** List of holdings to display */
  holdings: Holding[];
  /** Callback when edit button is clicked */
  onEdit: (holding: Holding) => void;
  /** Callback when delete button is clicked */
  onDelete: (holdingId: string) => void;
  /** Whether a mutation is in progress */
  isDisabled?: boolean;
}

/**
 * Format a date string for display.
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * HoldingsTable displays a table of portfolio holdings
 * with edit and delete actions.
 */
export function HoldingsTable({
  holdings,
  onEdit,
  onDelete,
  isDisabled = false,
}: HoldingsTableProps) {
  if (holdings.length === 0) {
    return (
      <div className={styles.emptyState}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
          <line x1="12" y1="22.08" x2="12" y2="12" />
        </svg>
        <h3>No holdings yet</h3>
        <p>Add your first holding to get started with portfolio analytics.</p>
      </div>
    );
  }

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Name</th>
            <th className={styles.hideMobile}>Asset Class</th>
            <th className={styles.hideMobile}>Sector</th>
            <th className={styles.hideTablet}>Broker</th>
            <th className={styles.hideTablet}>Purchase Date</th>
            <th className={styles.actionsHeader}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => (
            <tr key={holding.id}>
              <td className={styles.ticker}>{holding.ticker}</td>
              <td className={styles.name}>{holding.name}</td>
              <td className={styles.hideMobile}>{holding.asset_class}</td>
              <td className={styles.hideMobile}>{holding.sector}</td>
              <td className={styles.hideTablet}>{holding.broker}</td>
              <td className={styles.hideTablet}>{formatDate(holding.purchase_date)}</td>
              <td className={styles.actions}>
                <button
                  className={styles.editButton}
                  onClick={() => onEdit(holding)}
                  disabled={isDisabled}
                  aria-label={`Edit ${holding.ticker}`}
                  title="Edit"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
                <button
                  className={styles.deleteButton}
                  onClick={() => onDelete(holding.id)}
                  disabled={isDisabled}
                  aria-label={`Delete ${holding.ticker}`}
                  title="Delete"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  </svg>
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
