import type { Security } from '../securitiesApi';
import styles from './SecuritiesTable.module.css';

type TimePeriod = '1Y' | '5Y';

interface SecuritiesTableProps {
  securities: Security[];
  period: TimePeriod;
}

/**
 * Format a percentage value for display.
 */
function formatPercent(value: number | null): string {
  if (value === null) return '-';
  return `${value.toFixed(2)}%`;
}

/**
 * Format a decimal value for display.
 */
function formatDecimal(value: number | null, decimals: number = 2): string {
  if (value === null) return '-';
  return value.toFixed(decimals);
}

/**
 * Get the appropriate metric value based on the selected time period.
 */
function getMetricForPeriod(
  security: Security,
  metric: 'total_return' | 'vs_risk_free' | 'vs_sp500' | 'volatility' | 'sharpe',
  period: TimePeriod
): number | null {
  if (period === '1Y') {
    switch (metric) {
      case 'total_return':
        return security.total_return_1y_pct;
      case 'vs_risk_free':
        return security.return_vs_risk_free_1y_pct;
      case 'vs_sp500':
        return security.return_vs_sp500_1y_pct;
      case 'volatility':
        return security.volatility_1y_pct;
      case 'sharpe':
        return security.sharpe_ratio_1y;
    }
  } else {
    switch (metric) {
      case 'total_return':
        return security.total_return_5y_pct;
      case 'vs_risk_free':
        return security.return_vs_risk_free_5y_pct;
      case 'vs_sp500':
        return security.return_vs_sp500_5y_pct;
      case 'volatility':
        return security.volatility_5y_pct;
      case 'sharpe':
        return security.sharpe_ratio_5y;
    }
  }
}

/**
 * SecuritiesTable displays a table of available securities.
 */
export function SecuritiesTable({ securities, period }: SecuritiesTableProps) {
  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.headerCell}>Ticker</th>
            <th className={styles.headerCell}>Name</th>
            <th className={styles.headerCell}>Asset Class</th>
            <th className={styles.headerCell}>Category</th>
            <th className={`${styles.headerCell} ${styles.numericHeader}`}>Expense Ratio</th>
            <th className={`${styles.headerCell} ${styles.numericHeader}`}>Total Return</th>
            <th className={`${styles.headerCell} ${styles.numericHeader}`}>vs Risk-Free</th>
            <th className={`${styles.headerCell} ${styles.numericHeader}`}>vs S&P 500</th>
            <th className={`${styles.headerCell} ${styles.numericHeader}`}>Volatility</th>
            <th className={`${styles.headerCell} ${styles.numericHeader}`}>Sharpe Ratio</th>
          </tr>
        </thead>
        <tbody>
          {securities.map((security) => {
            const totalReturn = getMetricForPeriod(security, 'total_return', period);
            const vsRiskFree = getMetricForPeriod(security, 'vs_risk_free', period);
            const vsSP500 = getMetricForPeriod(security, 'vs_sp500', period);
            const volatility = getMetricForPeriod(security, 'volatility', period);
            const sharpe = getMetricForPeriod(security, 'sharpe', period);

            return (
              <tr key={security.ticker} className={styles.row}>
                <td className={`${styles.cell} ${styles.tickerCell}`}>
                  {security.ticker}
                </td>
                <td className={styles.cell}>{security.name}</td>
                <td className={styles.cell}>{security.asset_class}</td>
                <td className={styles.cell}>{security.category || '-'}</td>
                <td className={`${styles.cell} ${styles.numericCell}`}>
                  {formatPercent(security.expense_ratio)}
                </td>
                <td className={`${styles.cell} ${styles.numericCell} ${
                  totalReturn !== null && totalReturn >= 0
                    ? styles.positive
                    : styles.negative
                }`}>
                  {formatPercent(totalReturn)}
                </td>
                <td className={`${styles.cell} ${styles.numericCell} ${
                  vsRiskFree !== null && vsRiskFree >= 0
                    ? styles.positive
                    : styles.negative
                }`}>
                  {formatPercent(vsRiskFree)}
                </td>
                <td className={`${styles.cell} ${styles.numericCell} ${
                  vsSP500 !== null && vsSP500 >= 0
                    ? styles.positive
                    : styles.negative
                }`}>
                  {formatPercent(vsSP500)}
                </td>
                <td className={`${styles.cell} ${styles.numericCell}`}>
                  {formatPercent(volatility)}
                </td>
                <td className={`${styles.cell} ${styles.numericCell}`}>
                  {formatDecimal(sharpe)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
