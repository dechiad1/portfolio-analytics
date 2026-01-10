import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import type { TickerAnalytics } from '../../../shared/types';
import styles from './BenchmarkComparison.module.css';

interface BenchmarkComparisonProps {
  holdings: TickerAnalytics[];
}

interface ChartDataPoint {
  ticker: string;
  name: string;
  excessReturn: number;
}

/**
 * Custom tooltip for the bar chart.
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
        <span className={styles.tooltipLabel}>vs S&P 500:</span>
        <span
          className={`${styles.tooltipValue} ${
            data.excessReturn >= 0 ? styles.positive : styles.negative
          }`}
        >
          {data.excessReturn >= 0 ? '+' : ''}
          {data.excessReturn.toFixed(2)}%
        </span>
      </div>
    </div>
  );
}

/**
 * BenchmarkComparison displays a horizontal bar chart showing
 * each holding's excess return vs S&P 500 benchmark.
 */
export function BenchmarkComparison({ holdings }: BenchmarkComparisonProps) {
  // Sort holdings by excess return (vs_benchmark_pct)
  const chartData: ChartDataPoint[] = holdings
    .map((h) => ({
      ticker: h.ticker,
      name: h.name,
      excessReturn: h.vs_benchmark_pct,
    }))
    .sort((a, b) => b.excessReturn - a.excessReturn);

  if (chartData.length === 0) {
    return (
      <div className={styles.container}>
        <h3 className={styles.title}>Benchmark Comparison</h3>
        <div className={styles.empty}>
          <p>No holdings data available</p>
        </div>
      </div>
    );
  }

  // Calculate chart height based on number of holdings
  const barHeight = 40;
  const chartHeight = Math.max(300, chartData.length * barHeight + 60);

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Benchmark Comparison</h3>
      <p className={styles.subtitle}>Excess return vs S&P 500</p>
      <div className={styles.chartWrapper} style={{ height: chartHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 10, right: 30, bottom: 10, left: 60 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border)"
              horizontal={false}
            />
            <XAxis
              type="number"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
              tickLine={{ stroke: 'var(--color-border)' }}
              axisLine={{ stroke: 'var(--color-border)' }}
              tickFormatter={(value) => `${value}%`}
            />
            <YAxis
              type="category"
              dataKey="ticker"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-border)' }}
              width={50}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--color-bg-hover)' }} />
            <ReferenceLine x={0} stroke="var(--color-border)" strokeWidth={2} />
            <Bar dataKey="excessReturn" radius={[0, 4, 4, 0]} maxBarSize={30}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.excessReturn >= 0 ? '#22c55e' : '#ef4444'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
