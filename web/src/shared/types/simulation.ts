/**
 * Model types for return generation
 */
export type ModelType = 'gaussian' | 'student_t' | 'regime_switching';

/**
 * Expected return estimation method
 */
export type MuType = 'historical' | 'forward';

/**
 * Stress test scenarios
 */
export type ScenarioType = 'japan_lost_decade' | 'stagflation';

/**
 * Rebalancing frequency
 */
export type RebalanceFrequency = 'quarterly' | 'monthly';

/**
 * Ruin threshold type
 */
export type RuinThresholdType = 'percentage' | 'absolute';

/**
 * Request payload for creating simulation
 */
export interface SimulationCreateRequest {
  name?: string;
  horizon_years: number;
  num_paths: number;
  model_type: ModelType;
  scenario?: ScenarioType | null;
  rebalance_frequency?: RebalanceFrequency | null;
  mu_type: MuType;
  sample_paths_count: number;
  ruin_threshold?: number | null;
  ruin_threshold_type: RuinThresholdType;
}

/**
 * A single sample path from simulation
 */
export interface SamplePath {
  percentile: number;
  values: number[];
  terminal_value: number;
}

/**
 * Aggregated metrics from simulation
 */
export interface MetricsSummary {
  terminal_wealth_mean: number;
  terminal_wealth_median: number;
  terminal_wealth_percentiles: Record<number, number>;
  max_drawdown_mean: number;
  max_drawdown_percentiles: Record<number, number>;
  cvar_95: number;
  probability_of_ruin: number;
  ruin_threshold: number | null;
  ruin_threshold_type: string;
}

/**
 * Simulation summary (for list view, no sample_paths)
 */
export interface SimulationSummary {
  id: string;
  portfolio_id: string;
  name: string | null;
  horizon_years: number;
  num_paths: number;
  model_type: ModelType;
  scenario: ScenarioType | null;
  mu_type: MuType;
  metrics: MetricsSummary;
  created_at: string;
}

/**
 * Full simulation (includes sample_paths)
 */
export interface Simulation extends SimulationSummary {
  rebalance_frequency: RebalanceFrequency | null;
  sample_paths_count: number;
  ruin_threshold: number | null;
  ruin_threshold_type: RuinThresholdType;
  sample_paths: SamplePath[];
}

/**
 * Default simulation config
 */
export const DEFAULT_SIMULATION_CONFIG: SimulationCreateRequest = {
  horizon_years: 5,
  num_paths: 1000,
  model_type: 'gaussian',
  scenario: null,
  rebalance_frequency: null,
  mu_type: 'historical',
  sample_paths_count: 10,
  ruin_threshold: 0.30,
  ruin_threshold_type: 'percentage',
};

/**
 * Human-readable labels for model types
 */
export const MODEL_TYPE_LABELS: Record<ModelType, string> = {
  gaussian: 'Gaussian',
  student_t: 'Student-t (Fat Tails)',
  regime_switching: 'Regime Switching',
};

/**
 * Human-readable labels for scenarios
 */
export const SCENARIO_LABELS: Record<ScenarioType, string> = {
  japan_lost_decade: 'Japan Lost Decade',
  stagflation: 'Stagflation',
};

/**
 * Human-readable labels for mu types
 */
export const MU_TYPE_LABELS: Record<MuType, string> = {
  historical: 'Historical',
  forward: 'Forward (Analyst)',
};

/**
 * Human-readable labels for rebalance frequencies
 */
export const REBALANCE_FREQUENCY_LABELS: Record<RebalanceFrequency, string> = {
  quarterly: 'Quarterly',
  monthly: 'Monthly',
};
