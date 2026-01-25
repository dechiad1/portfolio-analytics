import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { SamplePath } from '../../../shared/types/simulation';
import styles from './SimulationChart.module.css';

interface SimulationChartProps {
  samplePaths: SamplePath[];
  horizonYears: number;
  initialValue?: number;
}

interface ChartDataPoint {
  year: number;
  [key: string]: number;
}

/**
 * Get color based on percentile.
 * Red for low, gray for middle, green for high.
 */
function getPercentileColor(percentile: number): string {
  if (percentile <= 15) return '#ef4444'; // Red
  if (percentile <= 25) return '#f97316'; // Orange
  if (percentile <= 45) return '#eab308'; // Yellow
  if (percentile <= 55) return '#9ca3af'; // Gray (median-ish)
  if (percentile <= 75) return '#84cc16'; // Light green
  return '#22c55e'; // Green
}

/**
 * Format currency for axis/tooltip.
 */
function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}k`;
  }
  return `$${value.toFixed(0)}`;
}

/**
 * Custom tooltip for the chart.
 */
function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: number;
}) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipHeader}>Year {label}</div>
      <div className={styles.tooltipContent}>
        {payload.map((entry) => (
          <div key={entry.name} className={styles.tooltipRow}>
            <span
              className={styles.tooltipDot}
              style={{ backgroundColor: entry.color }}
            />
            <span className={styles.tooltipLabel}>{entry.name}:</span>
            <span className={styles.tooltipValue}>{formatCurrency(entry.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * SimulationChart displays sample paths as line chart.
 */
export function SimulationChart({
  samplePaths,
  horizonYears,
  initialValue = 100000,
}: SimulationChartProps) {
  // Transform sample paths into chart data
  const chartData: ChartDataPoint[] = [];

  if (samplePaths.length > 0) {
    const numSteps = samplePaths[0].values.length;
    const yearsPerStep = horizonYears / (numSteps - 1);

    for (let i = 0; i < numSteps; i++) {
      const dataPoint: ChartDataPoint = {
        year: Math.round(i * yearsPerStep * 10) / 10,
      };

      samplePaths.forEach((path) => {
        dataPoint[`p${path.percentile}`] = path.values[i];
      });

      chartData.push(dataPoint);
    }
  }

  // Sort paths by percentile for legend ordering
  const sortedPaths = [...samplePaths].sort((a, b) => b.percentile - a.percentile);

  if (samplePaths.length === 0) {
    return (
      <div className={styles.container}>
        <h3 className={styles.title}>Sample Paths</h3>
        <div className={styles.empty}>
          <p>No sample paths available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Sample Paths</h3>
      <p className={styles.subtitle}>
        {samplePaths.length} representative paths at evenly-spaced percentiles
      </p>
      <div className={styles.legend}>
        <span className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#22c55e' }} />
          High percentiles (good outcomes)
        </span>
        <span className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#9ca3af' }} />
          Median
        </span>
        <span className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#ef4444' }} />
          Low percentiles (bad outcomes)
        </span>
      </div>
      <div className={styles.chartWrapper}>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 20, right: 30, bottom: 40, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis
              dataKey="year"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
              tickLine={{ stroke: 'var(--color-border)' }}
              axisLine={{ stroke: 'var(--color-border)' }}
              label={{
                value: 'Years',
                position: 'bottom',
                offset: 0,
                fill: 'var(--color-text-secondary)',
                fontSize: 12,
              }}
            />
            <YAxis
              tickFormatter={formatCurrency}
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
              tickLine={{ stroke: 'var(--color-border)' }}
              axisLine={{ stroke: 'var(--color-border)' }}
              label={{
                value: 'Portfolio Value ($)',
                angle: -90,
                position: 'insideLeft',
                fill: 'var(--color-text-secondary)',
                fontSize: 12,
                offset: 10,
              }}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={initialValue}
              stroke="var(--color-text-tertiary)"
              strokeDasharray="5 5"
              label={{
                value: 'Initial',
                position: 'right',
                fill: 'var(--color-text-tertiary)',
                fontSize: 10,
              }}
            />
            {sortedPaths.map((path) => (
              <Line
                key={path.percentile}
                type="monotone"
                dataKey={`p${path.percentile}`}
                name={`${path.percentile}th %ile`}
                stroke={getPercentileColor(path.percentile)}
                strokeWidth={path.percentile === 50 ? 2.5 : 1.5}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
