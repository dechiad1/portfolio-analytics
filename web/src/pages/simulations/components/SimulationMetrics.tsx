import type { MetricsSummary } from '../../../shared/types/simulation';
import { Tooltip } from '../../../shared/components/Tooltip';
import styles from './SimulationMetrics.module.css';

interface SimulationMetricsProps {
  metrics: MetricsSummary;
  initialValue?: number;
}

/**
 * Format a number as currency.
 */
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format a number as percentage.
 */
function formatPercentage(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
}

/**
 * SimulationMetrics displays key metrics from simulation results.
 */
export function SimulationMetrics({ metrics, initialValue = 100000 }: SimulationMetricsProps) {
  const {
    terminal_wealth_mean,
    terminal_wealth_median,
    terminal_wealth_percentiles,
    max_drawdown_mean,
    cvar_95,
    probability_of_ruin,
    ruin_threshold,
    ruin_threshold_type,
  } = metrics;

  const ruinThresholdDisplay = ruin_threshold !== null
    ? ruin_threshold_type === 'percentage'
      ? formatPercentage(ruin_threshold)
      : formatCurrency(ruin_threshold)
    : 'N/A';

  const medianReturn = ((terminal_wealth_median / initialValue) - 1);

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Simulation Metrics</h3>

      <div className={styles.grid}>
        {/* Terminal Wealth */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={styles.cardIcon}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23" />
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </span>
            <Tooltip content="The projected portfolio value at the end of your simulation horizon, based on running thousands of market scenarios.">
              <span className={styles.cardLabel}>Terminal Wealth</span>
            </Tooltip>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.mainValue}>
              <span className={styles.valueBig}>{formatCurrency(terminal_wealth_median)}</span>
              <Tooltip content="The median is the middle outcome - half of all simulations ended above this value, half below. More reliable than the mean for skewed distributions.">
                <span className={styles.valueHint}>median</span>
              </Tooltip>
            </div>
            <div className={styles.subValues}>
              <Tooltip content="The arithmetic average of all simulation outcomes. Can be skewed by extreme values.">
                <div className={styles.subValue}>
                  <span className={styles.subLabel}>Mean</span>
                  <span>{formatCurrency(terminal_wealth_mean)}</span>
                </div>
              </Tooltip>
              <Tooltip content="In the worst 5% of scenarios, your portfolio ended at or below this value. Use this to understand downside risk.">
                <div className={styles.subValue}>
                  <span className={styles.subLabel}>5th %ile</span>
                  <span>{formatCurrency(terminal_wealth_percentiles[5] || 0)}</span>
                </div>
              </Tooltip>
              <Tooltip content="In the best 5% of scenarios, your portfolio ended at or above this value. Represents optimistic outcomes.">
                <div className={styles.subValue}>
                  <span className={styles.subLabel}>95th %ile</span>
                  <span>{formatCurrency(terminal_wealth_percentiles[95] || 0)}</span>
                </div>
              </Tooltip>
            </div>
            <Tooltip content="The median percentage gain or loss relative to your starting portfolio value over the simulation period.">
              <div className={styles.returnBadge}>
                <span className={medianReturn >= 0 ? styles.positive : styles.negative}>
                  {medianReturn >= 0 ? '+' : ''}{formatPercentage(medianReturn)} return
                </span>
              </div>
            </Tooltip>
          </div>
        </div>

        {/* Risk Metrics */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={`${styles.cardIcon} ${styles.cardIconWarning}`}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </span>
            <Tooltip content="Key measures of portfolio risk and potential losses during the simulation period.">
              <span className={styles.cardLabel}>Risk Metrics</span>
            </Tooltip>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.riskGrid}>
              <Tooltip content="Maximum Drawdown measures the largest peak-to-trough decline your portfolio experienced. This is the average across all simulations. A 20% drawdown means at some point you were down 20% from a previous high.">
                <div className={styles.riskItem}>
                  <span className={styles.riskLabel}>Max Drawdown (avg)</span>
                  <span className={styles.riskValue}>{formatPercentage(max_drawdown_mean)}</span>
                </div>
              </Tooltip>
              <Tooltip content="Conditional Value at Risk (CVaR) at 95% shows the average portfolio value in the worst 5% of scenarios. This is your expected loss in tail-risk events - worse than the 5th percentile on average.">
                <div className={styles.riskItem}>
                  <span className={styles.riskLabel}>CVaR 95%</span>
                  <span className={styles.riskValue}>{formatCurrency(cvar_95)}</span>
                </div>
              </Tooltip>
            </div>
          </div>
        </div>

        {/* Probability of Ruin */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={`${styles.cardIcon} ${probability_of_ruin > 0.1 ? styles.cardIconDanger : styles.cardIconSuccess}`}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </span>
            <Tooltip content="The percentage of simulations where your portfolio fell below your specified ruin threshold at any point during the simulation - not just at the end. Lower is better.">
              <span className={styles.cardLabel}>Probability of Ruin</span>
            </Tooltip>
          </div>
          <div className={styles.cardBody}>
            <div className={styles.mainValue}>
              <span className={`${styles.valueBig} ${probability_of_ruin > 0.2 ? styles.valueDanger : probability_of_ruin > 0.1 ? styles.valueWarning : styles.valueSuccess}`}>
                {formatPercentage(probability_of_ruin)}
              </span>
            </div>
            <Tooltip content={`Your configured threshold. Simulations that dropped below ${ruinThresholdDisplay} of the starting value at any point are counted as "ruin" scenarios.`}>
              <p className={styles.ruinDescription}>
                Probability of falling below {ruinThresholdDisplay} at any point
              </p>
            </Tooltip>
          </div>
        </div>
      </div>
    </div>
  );
}
