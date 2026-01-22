import type { PortfolioSummary, BreakdownItem } from '../../../shared/types';
import styles from './BreakdownCharts.module.css';

interface BreakdownChartsProps {
  summary: PortfolioSummary;
}

// Colors for pie chart segments
const CHART_COLORS = [
  '#3b82f6', // blue
  '#22c55e', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
  '#14b8a6', // teal
  '#6366f1', // indigo
];

interface PieChartProps {
  data: BreakdownItem[];
  title: string;
}

/**
 * Format a number as currency (compact).
 */
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

/**
 * PieChart renders a simple SVG pie chart with legend.
 */
function PieChart({ data, title }: PieChartProps) {
  if (data.length === 0) {
    return (
      <div className={styles.chartCard}>
        <h3 className={styles.chartTitle}>{title}</h3>
        <p className={styles.emptyText}>No data available</p>
      </div>
    );
  }

  // Calculate pie segments
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let currentAngle = -90; // Start from top

  const segments = data.map((item, index) => {
    const percentage = total > 0 ? (item.value / total) * 100 : 0;
    const angle = (percentage / 100) * 360;
    const startAngle = currentAngle;
    const endAngle = currentAngle + angle;
    currentAngle = endAngle;

    // Calculate SVG arc path
    const startX = 50 + 40 * Math.cos((startAngle * Math.PI) / 180);
    const startY = 50 + 40 * Math.sin((startAngle * Math.PI) / 180);
    const endX = 50 + 40 * Math.cos((endAngle * Math.PI) / 180);
    const endY = 50 + 40 * Math.sin((endAngle * Math.PI) / 180);
    const largeArcFlag = angle > 180 ? 1 : 0;

    // For full circle (100%), draw a complete circle
    const path =
      percentage >= 99.9
        ? `M 50,10 A 40,40 0 1,1 49.99,10`
        : `M 50,50 L ${startX},${startY} A 40,40 0 ${largeArcFlag},1 ${endX},${endY} Z`;

    return {
      ...item,
      color: CHART_COLORS[index % CHART_COLORS.length],
      percentage,
      path,
    };
  });

  return (
    <div className={styles.chartCard}>
      <h3 className={styles.chartTitle}>{title}</h3>
      <div className={styles.chartContent}>
        <div className={styles.pieContainer}>
          <svg viewBox="0 0 100 100" className={styles.pie}>
            {segments.map((segment, index) => (
              <path
                key={index}
                d={segment.path}
                fill={segment.color}
                className={styles.segment}
              >
                <title>
                  {segment.name}: {formatCurrency(segment.value)} (
                  {segment.percentage.toFixed(1)}%)
                </title>
              </path>
            ))}
          </svg>
        </div>
        <ul className={styles.legend}>
          {segments.map((segment, index) => (
            <li key={index} className={styles.legendItem}>
              <span
                className={styles.legendColor}
                style={{ backgroundColor: segment.color }}
              />
              <span className={styles.legendLabel}>{segment.name}</span>
              <span className={styles.legendValue}>
                {segment.percentage.toFixed(1)}%
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/**
 * BreakdownCharts displays pie charts for portfolio breakdowns.
 */
export function BreakdownCharts({ summary }: BreakdownChartsProps) {
  return (
    <div className={styles.grid}>
      <PieChart data={summary.by_asset_type} title="By Asset Type" />
      <PieChart data={summary.by_asset_class} title="By Asset Class" />
      <PieChart data={summary.by_sector} title="By Sector" />
    </div>
  );
}
