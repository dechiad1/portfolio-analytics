import { useState, useCallback, useEffect } from 'react';
import type { SimulationCreateRequest, ModelType, ScenarioType, RebalanceFrequency, MuType, RuinThresholdType } from '../../../shared/types/simulation';
import { MODEL_TYPE_LABELS, SCENARIO_LABELS, MU_TYPE_LABELS, REBALANCE_FREQUENCY_LABELS } from '../../../shared/types/simulation';
import styles from './SimulationConfigModal.module.css';

interface SimulationConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: SimulationCreateRequest) => Promise<void>;
  isRunning: boolean;
  defaultConfig: SimulationCreateRequest;
}

/**
 * SimulationConfigModal provides a form to configure simulation parameters.
 */
export function SimulationConfigModal({
  isOpen,
  onClose,
  onSubmit,
  isRunning,
  defaultConfig,
}: SimulationConfigModalProps) {
  const [name, setName] = useState(defaultConfig.name || '');
  const [horizonYears, setHorizonYears] = useState(defaultConfig.horizon_years);
  const [ruinThreshold, setRuinThreshold] = useState(
    defaultConfig.ruin_threshold !== null && defaultConfig.ruin_threshold !== undefined
      ? (defaultConfig.ruin_threshold * 100).toString()
      : '30'
  );
  const [numPaths, setNumPaths] = useState(defaultConfig.num_paths);
  const [modelType, setModelType] = useState<ModelType>(defaultConfig.model_type);
  const [scenario, setScenario] = useState<ScenarioType | null>(defaultConfig.scenario || null);
  const [rebalanceFrequency, setRebalanceFrequency] = useState<RebalanceFrequency | null>(
    defaultConfig.rebalance_frequency || null
  );
  const [muType, setMuType] = useState<MuType>(defaultConfig.mu_type);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isRunning) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose, isRunning]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);

      const ruinThresholdValue = parseFloat(ruinThreshold);
      if (isNaN(ruinThresholdValue) || ruinThresholdValue < 0 || ruinThresholdValue > 100) {
        setError('Ruin threshold must be between 0 and 100%');
        return;
      }

      try {
        await onSubmit({
          name: name.trim() || undefined,
          horizon_years: horizonYears,
          num_paths: numPaths,
          model_type: modelType,
          scenario: scenario,
          rebalance_frequency: rebalanceFrequency,
          mu_type: muType,
          sample_paths_count: 10,
          ruin_threshold: ruinThresholdValue / 100,
          ruin_threshold_type: 'percentage' as RuinThresholdType,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to run simulation');
      }
    },
    [name, horizonYears, numPaths, modelType, scenario, rebalanceFrequency, muType, ruinThreshold, onSubmit]
  );

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !isRunning) {
        onClose();
      }
    },
    [onClose, isRunning]
  );

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={handleBackdropClick} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Run Simulation</h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            disabled={isRunning}
            aria-label="Close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Basic Settings</h3>

            <div className={styles.field}>
              <label htmlFor="name" className={styles.label}>
                Name (optional)
              </label>
              <input
                id="name"
                type="text"
                className={styles.input}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Simulation"
                disabled={isRunning}
                maxLength={255}
              />
            </div>

            <div className={styles.row}>
              <div className={styles.field}>
                <label htmlFor="horizonYears" className={styles.label}>
                  Horizon (years)
                </label>
                <input
                  id="horizonYears"
                  type="number"
                  className={styles.input}
                  value={horizonYears}
                  onChange={(e) => setHorizonYears(parseInt(e.target.value) || 1)}
                  min={1}
                  max={30}
                  required
                  disabled={isRunning}
                />
              </div>
              <div className={styles.field}>
                <label htmlFor="ruinThreshold" className={styles.label}>
                  Ruin Threshold (%)
                </label>
                <input
                  id="ruinThreshold"
                  type="number"
                  className={styles.input}
                  value={ruinThreshold}
                  onChange={(e) => setRuinThreshold(e.target.value)}
                  placeholder="30"
                  min={0}
                  max={100}
                  step={1}
                  disabled={isRunning}
                />
                <span className={styles.hint}>Probability of losing this % or more</span>
              </div>
            </div>
          </div>

          <button
            type="button"
            className={styles.advancedToggle}
            onClick={() => setShowAdvanced(!showAdvanced)}
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
              className={showAdvanced ? styles.rotated : ''}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
            Advanced Settings
          </button>

          {showAdvanced && (
            <div className={styles.section}>
              <div className={styles.row}>
                <div className={styles.field}>
                  <label htmlFor="numPaths" className={styles.label}>
                    Number of Paths
                  </label>
                  <input
                    id="numPaths"
                    type="number"
                    className={styles.input}
                    value={numPaths}
                    onChange={(e) => setNumPaths(parseInt(e.target.value) || 100)}
                    min={100}
                    max={10000}
                    step={100}
                    required
                    disabled={isRunning}
                  />
                  <span className={styles.hint}>100 - 10,000</span>
                </div>
                <div className={styles.field}>
                  <label htmlFor="modelType" className={styles.label}>
                    Model
                  </label>
                  <select
                    id="modelType"
                    className={styles.select}
                    value={modelType}
                    onChange={(e) => setModelType(e.target.value as ModelType)}
                    disabled={isRunning}
                  >
                    {(Object.entries(MODEL_TYPE_LABELS) as [ModelType, string][]).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className={styles.row}>
                <div className={styles.field}>
                  <label htmlFor="scenario" className={styles.label}>
                    Scenario
                  </label>
                  <select
                    id="scenario"
                    className={styles.select}
                    value={scenario || ''}
                    onChange={(e) => setScenario(e.target.value ? (e.target.value as ScenarioType) : null)}
                    disabled={isRunning}
                  >
                    <option value="">None (baseline)</option>
                    {(Object.entries(SCENARIO_LABELS) as [ScenarioType, string][]).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className={styles.field}>
                  <label htmlFor="rebalanceFrequency" className={styles.label}>
                    Rebalancing
                  </label>
                  <select
                    id="rebalanceFrequency"
                    className={styles.select}
                    value={rebalanceFrequency || ''}
                    onChange={(e) =>
                      setRebalanceFrequency(e.target.value ? (e.target.value as RebalanceFrequency) : null)
                    }
                    disabled={isRunning}
                  >
                    <option value="">None</option>
                    {(Object.entries(REBALANCE_FREQUENCY_LABELS) as [RebalanceFrequency, string][]).map(
                      ([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      )
                    )}
                  </select>
                </div>
              </div>

              <div className={styles.field}>
                <label htmlFor="muType" className={styles.label}>
                  Return Estimate
                </label>
                <select
                  id="muType"
                  className={styles.select}
                  value={muType}
                  onChange={(e) => setMuType(e.target.value as MuType)}
                  disabled={isRunning}
                >
                  {(Object.entries(MU_TYPE_LABELS) as [MuType, string][]).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <div className={styles.actions}>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={onClose}
              disabled={isRunning}
            >
              Cancel
            </button>
            <button type="submit" className={styles.submitButton} disabled={isRunning}>
              {isRunning ? (
                <>
                  <span className={styles.spinner} />
                  Running...
                </>
              ) : (
                'Run Simulation'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
