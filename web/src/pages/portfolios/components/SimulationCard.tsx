import { useNavigate } from 'react-router-dom';
import type { SimulationSummary } from '../../../shared/types/simulation';
import { MODEL_TYPE_LABELS, SCENARIO_LABELS } from '../../../shared/types/simulation';
import styles from './SimulationCard.module.css';

interface SimulationCardProps {
  simulation: SimulationSummary;
  onDelete: (id: string) => void;
  isDeleting: boolean;
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
 * SimulationCard displays a single simulation summary.
 */
export function SimulationCard({
  simulation,
  onDelete,
  isDeleting,
}: SimulationCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/portfolios/${simulation.portfolio_id}/simulations/${simulation.id}`);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this simulation?')) {
      onDelete(simulation.id);
    }
  };

  const displayName = simulation.name || `${MODEL_TYPE_LABELS[simulation.model_type]} ${simulation.horizon_years}yr`;
  const configSummary = [
    MODEL_TYPE_LABELS[simulation.model_type],
    `${simulation.horizon_years}yr`,
    simulation.scenario ? SCENARIO_LABELS[simulation.scenario] : null,
  ]
    .filter(Boolean)
    .join(', ');

  const { metrics } = simulation;
  const ruinProbability = metrics.probability_of_ruin;

  return (
    <div className={styles.card} onClick={handleClick} role="button" tabIndex={0}>
      <div className={styles.header}>
        <h3 className={styles.name} title={displayName}>
          {displayName}
        </h3>
        <button
          className={styles.deleteButton}
          onClick={handleDelete}
          disabled={isDeleting}
          title="Delete simulation"
          aria-label="Delete simulation"
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

      <p className={styles.config}>{configSummary}</p>

      <div className={styles.metrics}>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Median Terminal</span>
          <span className={styles.metricValue}>
            {formatCurrency(metrics.terminal_wealth_median)}
          </span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Prob. of Ruin</span>
          <span
            className={`${styles.metricValue} ${
              ruinProbability > 0.2
                ? styles.metricDanger
                : ruinProbability > 0.1
                ? styles.metricWarning
                : styles.metricSuccess
            }`}
          >
            {formatPercentage(ruinProbability)}
          </span>
        </div>
      </div>

      <p className={styles.timestamp}>
        {new Date(simulation.created_at).toLocaleDateString()}
      </p>
    </div>
  );
}
