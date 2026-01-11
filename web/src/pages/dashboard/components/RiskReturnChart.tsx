import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ZAxis,
  Cell,
} from 'recharts';
import type { TickerAnalytics } from '../../../shared/types';
import styles from './RiskReturnChart.module.css';

interface RiskReturnChartProps {
  holdings: TickerAnalytics[];
}

interface ChartDataPoint {
  ticker: string;
  name: string;
  volatility: number;
  return: number;
  sharpe: number;
}

/**
 * Get color based on Sharpe ratio.
 * Red for negative, yellow for mediocre, green for good.
 */
function getSharpeColor(sharpe: number): string {
  if (sharpe < 0) return '#ef4444'; // Red
  if (sharpe < 0.5) return '#f97316'; // Orange
  if (sharpe < 1) return '#eab308'; // Yellow
  if (sharpe < 1.5) return '#84cc16'; // Light green
  return '#22c55e'; // Green
}

/**
 * Custom tooltip component for the scatter chart.
 */
function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDataPoint }>;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;

  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipHeader}>
        <span className={styles.tooltipTicker}>{data.ticker}</span>
        <span className={styles.tooltipName}>{data.name}</span>
      </div>
      <div className={styles.tooltipContent}>
        <div className={styles.tooltipRow}>
          <span>Return:</span>
          <span
            className={data.return >= 0 ? styles.positive : styles.negative}
          >
            {data.return >= 0 ? '+' : ''}
            {data.return.toFixed(2)}%
          </span>
        </div>
        <div className={styles.tooltipRow}>
          <span>Volatility:</span>
          <span>{data.volatility.toFixed(2)}%</span>
        </div>
        <div className={styles.tooltipRow}>
          <span>Sharpe:</span>
          <span style={{ color: getSharpeColor(data.sharpe) }}>
            {data.sharpe.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * RiskReturnChart displays a scatter plot of holdings
 * with volatility (risk) on x-axis and return on y-axis.
 */
export function RiskReturnChart({ holdings }: RiskReturnChartProps) {
  const chartData: ChartDataPoint[] = holdings.map((h) => ({
    ticker: h.ticker,
    name: h.name,
    volatility: h.volatility_pct,
    return: h.annualized_return_pct,
    sharpe: h.sharpe_ratio,
  }));

  if (chartData.length === 0) {
    return (
      <div className={styles.container}>
        <h3 className={styles.title}>Risk vs Return</h3>
        <div className={styles.empty}>
          <p>No holdings data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Risk vs Return</h3>
      <p className={styles.subtitle}>
        Color indicates Sharpe ratio (red = low, green = high)
      </p>
      <div className={styles.chartWrapper}>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis
              type="number"
              dataKey="volatility"
              name="Volatility"
              unit="%"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
              tickLine={{ stroke: 'var(--color-border)' }}
              axisLine={{ stroke: 'var(--color-border)' }}
              label={{
                value: 'Volatility (%)',
                position: 'bottom',
                offset: 0,
                fill: 'var(--color-text-secondary)',
                fontSize: 12,
              }}
            />
            <YAxis
              type="number"
              dataKey="return"
              name="Return"
              unit="%"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
              tickLine={{ stroke: 'var(--color-border)' }}
              axisLine={{ stroke: 'var(--color-border)' }}
              label={{
                value: 'Annualized Return (%)',
                angle: -90,
                position: 'insideLeft',
                fill: 'var(--color-text-secondary)',
                fontSize: 12,
              }}
            />
            <ZAxis type="number" dataKey="sharpe" range={[60, 200]} />
            <Tooltip content={<CustomTooltip />} />
            <Scatter data={chartData}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getSharpeColor(entry.sharpe)} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
