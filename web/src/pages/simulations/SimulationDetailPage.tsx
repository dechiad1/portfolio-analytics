import { useParams, useNavigate, Link } from 'react-router-dom';
import { useSimulationDetailState } from './useSimulationDetailState';
import { SimulationMetrics } from './components/SimulationMetrics';
import { SimulationChart } from './components/SimulationChart';
import { MODEL_TYPE_LABELS, SCENARIO_LABELS, MU_TYPE_LABELS, REBALANCE_FREQUENCY_LABELS } from '../../shared/types/simulation';
import { LoadingSpinner } from '../../shared/components/LoadingSpinner';
import { ErrorMessage } from '../../shared/components/ErrorMessage';
import styles from './SimulationDetailPage.module.css';

/**
 * Format percentage for display.
 */
function formatPercentage(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * SimulationDetailPage displays full simulation results.
 */
export function SimulationDetailPage() {
  const { portfolioId, simulationId } = useParams<{
    portfolioId: string;
    simulationId: string;
  }>();
  const navigate = useNavigate();
  const { simulation, isLoading, error, isDeleting, handleDelete } = useSimulationDetailState(simulationId);

  const onDelete = async () => {
    if (window.confirm('Are you sure you want to delete this simulation?')) {
      const success = await handleDelete();
      if (success) {
        navigate(`/portfolios/${portfolioId}`);
      }
    }
  };

  if (isLoading) {
    return (
      <div className={styles.page}>
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !simulation) {
    return (
      <div className={styles.page}>
        <ErrorMessage message={error || 'Simulation not found'} />
        <Link to={`/portfolios/${portfolioId}`} className={styles.backLink}>
          Back to Portfolio
        </Link>
      </div>
    );
  }

  const displayName = simulation.name || `${MODEL_TYPE_LABELS[simulation.model_type]} ${simulation.horizon_years}yr`;

  // Get initial portfolio value from sample paths (first value of any path)
  const initialValue = simulation.sample_paths.length > 0 && simulation.sample_paths[0].values.length > 0
    ? simulation.sample_paths[0].values[0]
    : 100000;

  return (
    <div className={styles.page}>
      {/* Breadcrumb */}
      <nav className={styles.breadcrumb}>
        <Link to="/portfolios">Portfolios</Link>
        <span className={styles.breadcrumbSep}>/</span>
        <Link to={`/portfolios/${portfolioId}`}>Portfolio</Link>
        <span className={styles.breadcrumbSep}>/</span>
        <span>Simulation</span>
      </nav>

      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>{displayName}</h1>
          <p className={styles.timestamp}>
            Created {new Date(simulation.created_at).toLocaleString()}
          </p>
        </div>
        <button
          className={styles.deleteButton}
          onClick={onDelete}
          disabled={isDeleting}
          title="Delete simulation"
        >
          {isDeleting ? 'Deleting...' : 'Delete'}
        </button>
      </header>

      {/* Config Summary */}
      <section className={styles.configSection}>
        <h2 className={styles.sectionTitle}>Configuration</h2>
        <div className={styles.configGrid}>
          <div className={styles.configItem}>
            <span className={styles.configLabel}>Model</span>
            <span className={styles.configValue}>{MODEL_TYPE_LABELS[simulation.model_type]}</span>
          </div>
          <div className={styles.configItem}>
            <span className={styles.configLabel}>Horizon</span>
            <span className={styles.configValue}>{simulation.horizon_years} years</span>
          </div>
          <div className={styles.configItem}>
            <span className={styles.configLabel}>Paths</span>
            <span className={styles.configValue}>{simulation.num_paths.toLocaleString()}</span>
          </div>
          <div className={styles.configItem}>
            <span className={styles.configLabel}>Return Estimate</span>
            <span className={styles.configValue}>{MU_TYPE_LABELS[simulation.mu_type]}</span>
          </div>
          {simulation.scenario && (
            <div className={styles.configItem}>
              <span className={styles.configLabel}>Scenario</span>
              <span className={styles.configValue}>{SCENARIO_LABELS[simulation.scenario]}</span>
            </div>
          )}
          {simulation.rebalance_frequency && (
            <div className={styles.configItem}>
              <span className={styles.configLabel}>Rebalancing</span>
              <span className={styles.configValue}>
                {REBALANCE_FREQUENCY_LABELS[simulation.rebalance_frequency]}
              </span>
            </div>
          )}
          {simulation.ruin_threshold !== null && (
            <div className={styles.configItem}>
              <span className={styles.configLabel}>Ruin Threshold</span>
              <span className={styles.configValue}>
                {simulation.ruin_threshold_type === 'percentage'
                  ? formatPercentage(simulation.ruin_threshold)
                  : `$${simulation.ruin_threshold.toLocaleString()}`}
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Metrics */}
      <section className={styles.metricsSection}>
        <SimulationMetrics metrics={simulation.metrics} initialValue={initialValue} />
      </section>

      {/* Chart */}
      <section className={styles.chartSection}>
        <SimulationChart
          samplePaths={simulation.sample_paths}
          horizonYears={simulation.horizon_years}
          initialValue={initialValue}
        />
      </section>
    </div>
  );
}
