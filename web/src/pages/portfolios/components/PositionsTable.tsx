import type { Position } from '../../../shared/types';
import styles from './PortfolioHoldingsTable.module.css';

interface PositionsTableProps {
  positions: Position[];
  onDelete: (position: Position) => void;
  isDisabled?: boolean;
}

/**
 * PositionsTable displays portfolio positions in a table format.
 */
export function PositionsTable({
  positions,
  onDelete,
  isDisabled = false,
}: PositionsTableProps) {
  if (positions.length === 0) {
    return (
      <div className={styles.empty}>
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
          <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
        </svg>
        <p>No positions yet. Add your first position to start tracking.</p>
      </div>
    );
  }

  const formatCurrency = (value: number | null | undefined) => {
    if (value == null) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number | null | undefined) => {
    if (value == null) return '-';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Name</th>
            <th>Type</th>
            <th>Sector</th>
            <th className={styles.numericHeader}>Qty</th>
            <th className={styles.numericHeader}>Avg Cost</th>
            <th className={styles.numericHeader}>Current</th>
            <th className={styles.numericHeader}>Value</th>
            <th className={styles.numericHeader}>Gain/Loss</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) => {
            const gainLossPct = position.gain_loss_pct;
            const isPositive = gainLossPct != null && gainLossPct >= 0;

            return (
              <tr key={position.security_id}>
                <td className={styles.ticker}>{position.ticker}</td>
                <td className={styles.name}>{position.name}</td>
                <td>{position.asset_type}</td>
                <td>{position.sector || '-'}</td>
                <td className={styles.numeric}>{position.quantity}</td>
                <td className={styles.numeric}>{formatCurrency(position.avg_cost)}</td>
                <td className={styles.numeric}>{formatCurrency(position.current_price)}</td>
                <td className={styles.numeric}>{formatCurrency(position.market_value)}</td>
                <td className={`${styles.numeric} ${isPositive ? styles.positive : styles.negative}`}>
                  {formatCurrency(position.gain_loss)}
                  <span className={styles.percent}>({formatPercent(gainLossPct)})</span>
                </td>
                <td className={styles.actions}>
                  <button
                    className={styles.deleteButton}
                    onClick={() => onDelete(position)}
                    disabled={isDisabled}
                    title="Remove position"
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
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
