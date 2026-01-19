import type { PortfolioHolding } from '../../../shared/types';
import styles from './PortfolioHoldingsTable.module.css';

interface PortfolioHoldingsTableProps {
  holdings: PortfolioHolding[];
  onEdit: (holding: PortfolioHolding) => void;
  onDelete: (holdingId: string) => void;
  isDisabled: boolean;
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
 * Format a date.
 */
function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString();
}

/**
 * PortfolioHoldingsTable displays holdings with edit/delete actions.
 */
export function PortfolioHoldingsTable({
  holdings,
  onEdit,
  onDelete,
  isDisabled,
}: PortfolioHoldingsTableProps) {
  if (holdings.length === 0) {
    return (
      <div className={styles.empty}>
        <svg
          className={styles.emptyIcon}
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
          <line x1="8" y1="6" x2="21" y2="6" />
          <line x1="8" y1="12" x2="21" y2="12" />
          <line x1="8" y1="18" x2="21" y2="18" />
          <line x1="3" y1="6" x2="3.01" y2="6" />
          <line x1="3" y1="12" x2="3.01" y2="12" />
          <line x1="3" y1="18" x2="3.01" y2="18" />
        </svg>
        <p className={styles.emptyText}>
          No holdings yet. Add your first holding to start tracking.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.th}>Ticker</th>
            <th className={styles.th}>Name</th>
            <th className={styles.th}>Type</th>
            <th className={`${styles.th} ${styles.thRight}`}>Quantity</th>
            <th className={`${styles.th} ${styles.thRight}`}>Purchase Price</th>
            <th className={`${styles.th} ${styles.thRight}`}>Current Price</th>
            <th className={`${styles.th} ${styles.thRight}`}>Value</th>
            <th className={`${styles.th} ${styles.thRight}`}>Gain/Loss</th>
            <th className={styles.th}>Date</th>
            <th className={styles.th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => {
            const value = holding.quantity * holding.current_price;
            const cost = holding.quantity * holding.purchase_price;
            const gainLoss = value - cost;
            const gainLossPercent = cost > 0 ? (gainLoss / cost) * 100 : 0;
            const isPositive = gainLoss >= 0;

            return (
              <tr key={holding.id} className={styles.row}>
                <td className={styles.td}>
                  <span className={styles.ticker}>{holding.ticker}</span>
                </td>
                <td className={styles.td}>
                  <span className={styles.name}>{holding.name}</span>
                </td>
                <td className={styles.td}>
                  <span className={styles.badge}>{holding.asset_type}</span>
                </td>
                <td className={`${styles.td} ${styles.tdRight}`}>
                  {holding.quantity.toLocaleString()}
                </td>
                <td className={`${styles.td} ${styles.tdRight}`}>
                  {formatCurrency(holding.purchase_price)}
                </td>
                <td className={`${styles.td} ${styles.tdRight}`}>
                  {formatCurrency(holding.current_price)}
                </td>
                <td className={`${styles.td} ${styles.tdRight}`}>
                  {formatCurrency(value)}
                </td>
                <td
                  className={`${styles.td} ${styles.tdRight} ${
                    isPositive ? styles.positive : styles.negative
                  }`}
                >
                  {formatCurrency(gainLoss)}
                  <span className={styles.percent}>
                    ({gainLossPercent >= 0 ? '+' : ''}
                    {gainLossPercent.toFixed(2)}%)
                  </span>
                </td>
                <td className={styles.td}>{formatDate(holding.purchase_date)}</td>
                <td className={styles.td}>
                  <div className={styles.actions}>
                    <button
                      className={styles.actionButton}
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
                      className={`${styles.actionButton} ${styles.deleteButton}`}
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
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
