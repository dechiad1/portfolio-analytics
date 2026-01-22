import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { AssetClassBreakdown, SectorBreakdown } from '../../../shared/types';
import styles from './AssetAllocationChart.module.css';

interface AssetAllocationChartProps {
  assetClassBreakdown: AssetClassBreakdown[];
  sectorBreakdown: SectorBreakdown[];
}

/**
 * Color palette for pie charts.
 */
const COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316', // Orange
  '#6366f1', // Indigo
];

interface ChartDataPoint {
  name: string;
  value: number;
  avgReturn: number;
}

/**
 * Custom tooltip for pie charts.
 */
function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDataPoint; name: string; value: number }>;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;

  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipName}>{data.name}</div>
      <div className={styles.tooltipRow}>
        <span>Holdings:</span>
        <span>{data.value}</span>
      </div>
      <div className={styles.tooltipRow}>
        <span>Avg Return:</span>
        <span className={data.avgReturn >= 0 ? styles.positive : styles.negative}>
          {data.avgReturn >= 0 ? '+' : ''}
          {data.avgReturn.toFixed(2)}%
        </span>
      </div>
    </div>
  );
}

/**
 * Custom legend renderer.
 */
function renderLegend(props: { payload?: Array<{ value: string; color?: string }> }) {
  const { payload } = props;
  if (!payload) return null;

  return (
    <ul className={styles.legend}>
      {payload.map((entry, index) => (
        <li key={`legend-${index}`} className={styles.legendItem}>
          <span
            className={styles.legendColor}
            style={{ backgroundColor: entry.color ?? '#999' }}
          />
          <span className={styles.legendLabel}>{entry.value}</span>
        </li>
      ))}
    </ul>
  );
}

/**
 * AssetAllocationChart displays two pie charts showing
 * holdings breakdown by asset class and sector.
 */
export function AssetAllocationChart({
  assetClassBreakdown,
  sectorBreakdown,
}: AssetAllocationChartProps) {
  const assetClassData: ChartDataPoint[] = assetClassBreakdown.map((item) => ({
    name: item.asset_class,
    value: item.count,
    avgReturn: item.avg_return,
  }));

  const sectorData: ChartDataPoint[] = sectorBreakdown.map((item) => ({
    name: item.sector,
    value: item.count,
    avgReturn: item.avg_return,
  }));

  const hasData = assetClassData.length > 0 || sectorData.length > 0;

  if (!hasData) {
    return (
      <div className={styles.container}>
        <h3 className={styles.title}>Asset Allocation</h3>
        <div className={styles.empty}>
          <p>No holdings data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Asset Allocation</h3>
      <div className={styles.chartsGrid}>
        <div className={styles.chartSection}>
          <h4 className={styles.chartSubtitle}>By Asset Class</h4>
          {assetClassData.length > 0 ? (
            <div className={styles.chartWrapper}>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={assetClassData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                    nameKey="name"
                  >
                    {assetClassData.map((_, index) => (
                      <Cell
                        key={`cell-asset-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend content={renderLegend} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className={styles.empty}>No data</div>
          )}
        </div>

        <div className={styles.chartSection}>
          <h4 className={styles.chartSubtitle}>By Sector</h4>
          {sectorData.length > 0 ? (
            <div className={styles.chartWrapper}>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={sectorData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                    nameKey="name"
                  >
                    {sectorData.map((_, index) => (
                      <Cell
                        key={`cell-sector-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend content={renderLegend} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className={styles.empty}>No data</div>
          )}
        </div>
      </div>
    </div>
  );
}
