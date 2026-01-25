# PR-2: Basic Portfolio Simulation

Remember to read the content in CLAUDE.md, .claude/agents & .claude/reference FIRST to understand the coding conventions, desired repository structures & goal of the project

### Completion
when all the tasks are fully complete & tested, print just DONEZO.

DO NOT SKIP THIS STEP. IT IS REQUIRED WHEN FULLY COMPLETE


## Overview
Implement a portfolio stress-testing simulation engine that allows users to answer:
- What is the probability I'm down 30% at any point in the next 5 years?
- How often do I fail a "must have above $X" constraint?
- What does recovery time look like for the worst drops?

---

## 1. Packaging & Architecture

**Decision:** Option A - Monorepo sibling package

```
portfolio-analytics/
├── api/                      # existing
├── simulation/               # new package
│   ├── pyproject.toml
│   └── src/simulation/
├── portfolio_analytics/      # existing dbt
└── docker/
```

- API imports simulation as a local dependency
- Single process, single Docker image
- Clean data in/out API enables future migration to worker pattern
- CPU-heavy work offloaded via `run_in_executor`

---

## 2. Data Pipeline (dbt)

### 2a. New Ingestion Script

**File:** `portfolio_analytics/scripts/ingest_analyst_targets.py`

Fetches from yfinance per ticker:
- `currentPrice`
- `targetMeanPrice` (12-month analyst target)
- `targetHighPrice`
- `targetLowPrice`
- `numberOfAnalystOpinions`

Loads to: `raw_analyst_targets` table in DuckDB

Run frequency: Weekly (analyst targets update infrequently)

### 2b. New dbt Models

**Staging:**
- `stg_analyst_targets.sql` - clean raw_analyst_targets

**Marts:**

| Mart | Description | Source |
|------|-------------|--------|
| `security_historical_mu` | Annualized mean return | `int_daily_returns` |
| `security_forward_mu` | Implied return from analyst targets | `stg_analyst_targets` |
| `security_volatility` | Annualized std dev | `int_daily_returns` |

**security_historical_mu.sql:**
```sql
select
    ticker,
    avg(daily_return) * 252 as annualized_mu,
    count(*) as observation_count,
    min(date) as data_start,
    max(date) as data_end
from {{ ref('int_daily_returns') }}
group by ticker
```

**security_volatility.sql:**
```sql
select
    ticker,
    stddev(daily_return) * sqrt(252) as annualized_volatility,
    count(*) as observation_count
from {{ ref('int_daily_returns') }}
group by ticker
```

**security_forward_mu.sql:**
```sql
select
    ticker,
    (target_mean_price / current_price) - 1 as forward_mu,
    analyst_count,
    fetched_at
from {{ ref('stg_analyst_targets') }}
where target_mean_price is not null
  and current_price is not null
  and current_price > 0
```

### 2c. On-demand (API layer)
- Correlation matrix computed at simulation time from historical returns
- Combined with pre-computed volatility to form full covariance matrix

---

## 3. Simulation Package Structure

```
simulation/
├── pyproject.toml
├── src/simulation/
│   ├── __init__.py
│   ├── models/                 # Return generators
│   │   ├── __init__.py
│   │   ├── base.py             # ReturnModel protocol
│   │   ├── gaussian.py         # GaussianMVNModel
│   │   ├── student_t.py        # StudentTMVNModel
│   │   └── regime_switching.py # RegimeSwitchingModel
│   ├── scenarios/              # Parameter overrides
│   │   ├── __init__.py
│   │   ├── base.py             # Scenario protocol
│   │   ├── japan_lost_decade.py
│   │   └── stagflation.py
│   ├── engine/                 # Core simulation loop
│   │   ├── __init__.py
│   │   ├── simulator.py        # Main runner
│   │   ├── rebalancer.py       # Rebalancing logic
│   │   └── frictions.py        # Transaction costs, fees
│   ├── results/                # Output handling
│   │   ├── __init__.py
│   │   ├── paths.py            # Path storage
│   │   └── metrics.py          # Summary statistics
│   └── types.py                # Shared dataclasses
└── tests/
```

**Key interfaces:**

```python
# models/base.py
class ReturnModel(Protocol):
    def sample_returns(self, state: State, params: Params, t: int, rng: Generator) -> np.ndarray: ...
    def update_state(self, state: State, returns: np.ndarray) -> State: ...

# scenarios/base.py
class Scenario(Protocol):
    def apply(self, params: Params, state: State, t: int) -> Params: ...
    def apply_shock(self, state: State, t: int) -> np.ndarray | None: ...

# engine/simulator.py
class Simulator:
    def run(self, request: SimulationRequest) -> SimulationResult: ...
```

**Time & steps:**
- Simulator takes `steps` (time-unit agnostic)
- API converts user's `horizon_years` to steps (e.g., 5 years → 20 quarterly steps)

**Rebalancing:**
- Occurs at each step, but only if weights drifted > 5% from target
- Transaction costs applied only when rebalance executes

**State (persisted across steps):**
- `current_regime` - for regime-switching model (calm/crisis)
- `current_weights` - drift from returns
- `portfolio_value` - running total

---

## 4. API Integration

**New files:**

| Layer | File | Purpose |
|-------|------|---------|
| Router | `api/routers/simulations.py` | HTTP endpoints |
| Schema | `api/schemas/simulation.py` | Request/response models |
| Service | `domain/services/simulation_service.py` | Orchestration |
| Port | `domain/ports/simulation_params_repository.py` | Fetch mu/vol from dbt |
| Adapter | `adapters/duckdb/simulation_params_repository.py` | DuckDB implementation |

**Endpoint:**

```
POST /api/portfolios/{portfolio_id}/simulations
```

**Request:**
```python
class SimulationRequest(BaseModel):
    horizon_years: int                    # e.g., 5
    num_paths: int                        # e.g., 1000
    model_type: ModelType                 # gaussian | student_t | regime_switching
    scenario: ScenarioType | None         # japan_lost_decade | stagflation | None
    rebalance_frequency: str | None       # quarterly | monthly | None
    mu_type: MuType = "historical"        # historical | forward
    sample_paths_count: int = 10          # number of representative paths to return
    ruin_threshold: float | None          # threshold for probability of ruin
    ruin_threshold_type: str = "percentage"  # "percentage" or "absolute"
```

**Representative path selection:**
- Paths ranked by terminal value
- Select paths at evenly-spaced percentiles (e.g., 10 paths → 5th, 15th, 25th, ... 95th)
- Each returned path labeled with its percentile

**Response:**
```python
class SimulationResponse(BaseModel):
    metrics: MetricsSummary
    sample_paths: list[SamplePath]  # representative paths

class SamplePath(BaseModel):
    percentile: int                  # which percentile this represents
    values: list[float]              # portfolio value at each time step
    terminal_value: float

class MetricsSummary(BaseModel):
    terminal_wealth_mean: float
    terminal_wealth_median: float
    terminal_wealth_percentiles: dict[int, float]  # 5, 25, 75, 95
    max_drawdown_mean: float
    max_drawdown_percentiles: dict[int, float]
    cvar_95: float
    probability_of_ruin: float       # below threshold
    ruin_threshold: float            # user-specified (% or absolute)
    ruin_threshold_type: str         # "percentage" or "absolute"
    # ...
```

**Service flow:**
1. Fetch portfolio holdings (securities + weights)
2. Fetch mu and volatility from dbt marts
3. Fetch historical returns, compute correlation matrix
4. Build SimulationRequest with full params
5. Call simulation package
6. Return results

---

## 5. Portfolio → Simulation Params

**Question:** How do we map a user's portfolio to simulation parameters?

Portfolio in postgres:
- Holdings: security_id, quantity
- Need: weights, mu, cov

**Flow:**
1. Fetch holdings for portfolio
2. Calculate weights from current prices: `weight_i = (quantity_i * price_i) / total_value`
3. Fetch mu, volatility per security from dbt
4. Fetch historical returns for correlation computation
5. Build params object for simulation

---

## 6. Testing Strategy

**Unit tests (simulation package):**

| Test | Validates |
|------|-----------|
| Seed reproducibility | Same seed → identical paths |
| Output shapes | N assets, T steps, P paths → correct dimensions |
| Regime transitions | Frequencies ≈ transition matrix over many steps |
| Fat tails | Student-t kurtosis > Gaussian kurtosis |
| Rebalancing tolerance | No rebalance when drift < 5%, rebalance when > 5% |
| Scenario overrides | Japan reduces mu, stagflation increases vol |
| Frictions | Transaction costs only when rebalance occurs |

**Unit tests (API data contract):**

| Test | Validates |
|------|-----------|
| Request validation | Required fields, types, enums |
| Request limits | 400 when exceeding max paths/horizon |
| Response schema | MetricsSummary has all expected fields |
| SamplePath structure | percentile, values, terminal_value present |
| Ruin threshold types | Both "percentage" and "absolute" accepted |
| Edge cases | Empty portfolio, single security, zero holdings |

**Integration tests (API):**
- End-to-end simulation request with real dbt data
- Correct params fetched from marts
- Full response structure valid

**Example script:**
- `simulation/examples/compare_models.py`
- 3-asset example comparing Gaussian vs Student-t vs Regime-switching
- Print summary metrics for each model/scenario combination

---

## 7. Files to Create/Modify

**New files:**
- `simulation/` - entire new package (see Section 3 for structure)
- `simulation/examples/compare_models.py` - example script
- `api/api/routers/simulations.py`
- `api/api/schemas/simulation.py`
- `api/domain/services/simulation_service.py`
- `api/domain/ports/simulation_params_repository.py`
- `api/adapters/duckdb/simulation_params_repository.py`
- `portfolio_analytics/scripts/ingest_analyst_targets.py`
- `portfolio_analytics/dbt/models/staging/stg_analyst_targets.sql`
- `portfolio_analytics/dbt/models/marts/security_historical_mu.sql`
- `portfolio_analytics/dbt/models/marts/security_forward_mu.sql`
- `portfolio_analytics/dbt/models/marts/security_volatility.sql`

**Modified files:**
- `api/pyproject.toml` - add simulation dependency
- `api/main.py` - register simulation router
- `docker/` - ensure simulation package included in image
- `portfolio_analytics/dbt/models/sources.yml` - add raw_analyst_targets source

---

## 8. Verification

1. **Unit tests:** `cd simulation && pytest`
2. **Ingestion:** `python portfolio_analytics/scripts/ingest_analyst_targets.py`
3. **dbt:** `cd portfolio_analytics/dbt && dbt run --select stg_analyst_targets security_historical_mu security_forward_mu security_volatility`
4. **API tests:** `cd api && pytest tests/test_simulations.py`
5. **Manual test:**
   - Create portfolio with holdings
   - POST simulation request
   - Verify metrics returned

---

## 9. Limits & Defaults

| Parameter | Default | Max |
|-----------|---------|-----|
| `num_paths` | 1,000 | 10,000 |
| `horizon_years` | 5 | 30 |
| `sample_paths_count` | 10 | 50 |

Validation at API layer - return 400 if exceeded.

---

## 10. React UI

### 10a. Overview

Simulation feature with persistence and multi-page experience:

1. **Portfolio Detail Page** - Shows simulation cards (one per saved run)
2. **Simulation Detail Page** - Full exploration when clicking a card
3. **Config Modal** - Modal form for configuring simulation parameters
4. **Persistence** - Simulations stored in Postgres for history & comparison

### 10b. Backend Additions for Persistence

**New Postgres Table:** `simulations`

```sql
CREATE TABLE simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    name VARCHAR(255),  -- optional user-provided name

    -- Request params
    horizon_years INTEGER NOT NULL,
    num_paths INTEGER NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    scenario VARCHAR(50),
    rebalance_frequency VARCHAR(50),
    mu_type VARCHAR(50) NOT NULL,
    sample_paths_count INTEGER NOT NULL,
    ruin_threshold FLOAT,
    ruin_threshold_type VARCHAR(50) NOT NULL,

    -- Results (stored as JSONB)
    metrics JSONB NOT NULL,
    sample_paths JSONB NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_portfolio FOREIGN KEY (portfolio_id)
        REFERENCES portfolios(id) ON DELETE CASCADE
);

CREATE INDEX idx_simulations_portfolio_id ON simulations(portfolio_id);
```

**New Alembic Migration:** `api/alembic/versions/xxx_add_simulations_table.py`

**Updated API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/portfolios/{id}/simulations` | Run simulation + save to DB |
| GET | `/portfolios/{id}/simulations` | List simulations for portfolio |
| GET | `/simulations/{id}` | Get single simulation with full results |
| DELETE | `/simulations/{id}` | Delete simulation (with ownership check) |
| PATCH | `/simulations/{id}` | Rename simulation |

**Response changes:**
- POST returns saved simulation with `id` field
- GET list returns summary (no sample_paths for list view)
- GET single returns full results including sample_paths

### 10c. New Files

```
web/src/
├── shared/types/simulation.ts           # TypeScript types
├── pages/portfolios/
│   ├── simulationApi.ts                 # API functions
│   └── components/
│       ├── SimulationsSection.tsx       # Card list on portfolio detail
│       ├── SimulationsSection.module.css
│       ├── SimulationCard.tsx           # Single simulation card
│       ├── SimulationCard.module.css
│       ├── SimulationConfigModal.tsx    # Config form modal
│       └── SimulationConfigModal.module.css
├── pages/simulations/
│   ├── SimulationDetailPage.tsx         # Full simulation view
│   ├── SimulationDetailPage.module.css
│   ├── useSimulationDetailState.ts      # State hook
│   └── components/
│       ├── SimulationMetrics.tsx        # Metrics cards
│       ├── SimulationMetrics.module.css
│       ├── SimulationChart.tsx          # Sample paths chart
│       └── SimulationChart.module.css
```

### 10d. TypeScript Types

**File:** `web/src/shared/types/simulation.ts`

```typescript
/** Model types for return generation */
export type ModelType = 'gaussian' | 'student_t' | 'regime_switching';

/** Expected return estimation method */
export type MuType = 'historical' | 'forward';

/** Stress test scenarios */
export type ScenarioType = 'japan_lost_decade' | 'stagflation';

/** Rebalancing frequency */
export type RebalanceFrequency = 'quarterly' | 'monthly';

/** Ruin threshold type */
export type RuinThresholdType = 'percentage' | 'absolute';

/** Request payload for creating simulation */
export interface SimulationCreateRequest {
  name?: string;  // optional custom name
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

/** A single sample path from simulation */
export interface SamplePath {
  percentile: number;
  values: number[];
  terminal_value: number;
}

/** Aggregated metrics from simulation */
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

/** Simulation summary (for list view, no sample_paths) */
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

/** Full simulation (includes sample_paths) */
export interface Simulation extends SimulationSummary {
  rebalance_frequency: RebalanceFrequency | null;
  sample_paths_count: number;
  ruin_threshold: number | null;
  ruin_threshold_type: RuinThresholdType;
  sample_paths: SamplePath[];
}

/** Default simulation config */
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

/** Human-readable labels for model types */
export const MODEL_TYPE_LABELS: Record<ModelType, string> = {
  gaussian: 'Gaussian',
  student_t: 'Student-t (Fat Tails)',
  regime_switching: 'Regime Switching',
};

/** Human-readable labels for scenarios */
export const SCENARIO_LABELS: Record<ScenarioType, string> = {
  japan_lost_decade: 'Japan Lost Decade',
  stagflation: 'Stagflation',
};
```

### 10e. API Functions

**File:** `web/src/pages/portfolios/simulationApi.ts`

```typescript
import { api } from '../../shared/api/client';
import type {
  SimulationCreateRequest,
  Simulation,
  SimulationSummary,
} from '../../shared/types/simulation';

/** Create and run a new simulation */
export async function createSimulation(
  portfolioId: string,
  request: SimulationCreateRequest
): Promise<Simulation> {
  return api.post<Simulation>(
    `/portfolios/${portfolioId}/simulations`,
    request
  );
}

/** List simulations for a portfolio */
export async function listSimulations(
  portfolioId: string
): Promise<SimulationSummary[]> {
  return api.get<SimulationSummary[]>(
    `/portfolios/${portfolioId}/simulations`
  );
}

/** Get a single simulation with full results */
export async function getSimulation(
  simulationId: string
): Promise<Simulation> {
  return api.get<Simulation>(`/simulations/${simulationId}`);
}

/** Delete a simulation */
export async function deleteSimulation(
  simulationId: string
): Promise<void> {
  return api.delete(`/simulations/${simulationId}`);
}

/** Rename a simulation */
export async function renameSimulation(
  simulationId: string,
  name: string
): Promise<Simulation> {
  return api.patch<Simulation>(
    `/simulations/${simulationId}`,
    { name }
  );
}
```

### 10f. Component Structure

**SimulationsSection** (portfolio detail page):
- Header: "Simulations" title + "New Simulation" button
- Empty state when no simulations exist
- Grid of SimulationCard components
- Loading state while fetching

**SimulationCard**:
- Displays: name (or auto-generated), model type, horizon, key metrics
- Key metrics shown: Terminal Wealth (median), Probability of Ruin
- Config summary: "Gaussian, 5yr, Historical"
- Click navigates to detail page
- Delete button (with confirmation)

**SimulationConfigModal**:
- Basic fields (visible by default):
  - Name: text input (optional)
  - Horizon (years): number input, 1-30
  - Ruin Threshold: number input (percentage)
- Advanced toggle reveals:
  - Paths: number input, 100-10,000
  - Model: select (Gaussian, Student-t, Regime Switching)
  - Scenario: select (None, Japan Lost Decade, Stagflation)
  - Rebalancing: select (None, Quarterly, Monthly)
  - Return Estimate: select (Historical, Forward/Analyst)
- "Run Simulation" button
- "Cancel" button

**SimulationDetailPage** (`/portfolios/:portfolioId/simulations/:simulationId`):
- Breadcrumb: Portfolios > {portfolio name} > Simulations > {simulation name}
- Header with simulation name + delete button
- Config summary panel showing parameters used
- SimulationMetrics component
- SimulationChart component (10 sample paths)

**SimulationMetrics**:
- Cards grid showing:
  - Terminal Wealth: mean, median, 5th/95th percentile
  - Max Drawdown (mean)
  - CVaR 95%
  - Probability of Ruin (with threshold)

**SimulationChart**:
- Recharts `LineChart` with `ResponsiveContainer`
- X-axis: time steps labeled as "Year 0", "Year 1", etc.
- Y-axis: portfolio value ($) with currency formatting
- Horizontal dashed reference line at initial portfolio value (starting point)
- 10 lines for sample paths, colored by percentile:
  - Low percentiles (5th-25th): red/orange gradient
  - Middle (50th): neutral gray
  - High percentiles (75th-95th): green gradient
- Tooltip showing percentile + value at hover point
- Legend showing percentile ranges

### 10g. Routing

**Add to App.tsx:**

```tsx
<Route
  path="/portfolios/:portfolioId/simulations/:simulationId"
  element={<SimulationDetailPage />}
/>
```

### 10h. Integration with Portfolio Detail

**Modify:** `PortfolioDetailPage.tsx`

Add SimulationsSection after RiskAnalysisSection:

```tsx
import { SimulationsSection } from './components/SimulationsSection';

// After RiskAnalysisSection:
<section className={styles.section}>
  <SimulationsSection
    portfolioId={portfolioId!}
    hasHoldings={holdings.length > 0}
  />
</section>
```

### 10i. Styling Guidelines

- Card styles: match existing SummaryCards pattern
- Modal: match AddHoldingModal pattern
- Chart: min-height 400px, responsive container
- Use design tokens from index.css
- Percentile colors: CSS custom properties for theme consistency

### 10j. Testing

**Manual testing:**
1. Navigate to portfolio with holdings
2. Click "New Simulation" - verify modal opens
3. Configure with defaults, run - verify card appears
4. Click card - verify detail page loads
5. Verify chart shows 10 sample paths with correct colors
6. Verify metrics match what was shown on card
7. Delete simulation - verify confirmation and removal
8. Run multiple simulations - verify all appear as cards

**Edge cases:**
- No holdings: "New Simulation" disabled with tooltip
- API error during run: error message in modal
- Long simulation name: truncate on card, full on detail
- Many simulations: verify card grid handles overflow

---

## 11. Files Summary (Updated)

**Backend (Sections 1-9) - COMPLETED:**
- `simulation/` - entire package
- `api/` - router, schema, service, ports, adapters
- `portfolio_analytics/` - ingestion script, dbt models
- `Taskfile.yml` - fetch:analyst-targets task

**Backend (Section 10 additions) - NEW:**
- `api/alembic/versions/xxx_add_simulations_table.py` - migration
- `api/domain/entities/simulation.py` - entity class
- `api/api/schemas/simulation.py` - updated with persistence fields
- `api/api/routers/simulations.py` - updated with CRUD endpoints
- `api/domain/ports/simulation_repository.py` - port interface
- `api/adapters/postgres/simulation_repository.py` - Postgres adapter

**Frontend (Section 10) - NEW:**
- `web/src/shared/types/simulation.ts`
- `web/src/pages/portfolios/simulationApi.ts`
- `web/src/pages/portfolios/components/SimulationsSection.tsx`
- `web/src/pages/portfolios/components/SimulationsSection.module.css`
- `web/src/pages/portfolios/components/SimulationCard.tsx`
- `web/src/pages/portfolios/components/SimulationCard.module.css`
- `web/src/pages/portfolios/components/SimulationConfigModal.tsx`
- `web/src/pages/portfolios/components/SimulationConfigModal.module.css`
- `web/src/pages/simulations/SimulationDetailPage.tsx`
- `web/src/pages/simulations/SimulationDetailPage.module.css`
- `web/src/pages/simulations/useSimulationDetailState.ts`
- `web/src/pages/simulations/components/SimulationMetrics.tsx`
- `web/src/pages/simulations/components/SimulationMetrics.module.css`
- `web/src/pages/simulations/components/SimulationChart.tsx`
- `web/src/pages/simulations/components/SimulationChart.module.css`

**Modified:**
- `web/src/App.tsx` - add simulation detail route
- `web/src/pages/portfolios/PortfolioDetailPage.tsx` - add SimulationsSection
