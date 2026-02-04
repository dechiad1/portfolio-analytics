## Domain-Driven Design

#### Summary

This application consists of two major bounded contexts serving different purposes:
- **OLTP (api/)**: Transactional system for portfolio management - user interactions, position tracking, simulation execution, risk analysis
- **OLAP (portfolio_analytics/dbt/)**: Analytical system for market data processing - price history, performance metrics, risk parameters

These contexts are loosely coupled through well-defined ports. The OLTP system owns transactional state; the OLAP system owns derived analytics.

---

## Bounded Contexts

### 1. Portfolio Management Context (OLTP)

#### User Aggregate
```
User (root)
  |-- id, email, password_hash
  |-- oauth_provider, oauth_subject
  |-- is_admin
```
- Owns authentication and authorization
- Referenced by Portfolio via `user_id`
- No cascade deletes - portfolios are soft-deleted or orphaned

#### Portfolio Aggregate
```
Portfolio (root)
  |-- id, name, base_currency
  |-- user_id (references User)
  |
  +-- Position[] (within aggregate boundary)
        |-- security_id, quantity, avg_cost
        |-- Derived: cost_basis, market_value, gain_loss
```
- Portfolio is the aggregate root
- Positions belong to exactly one portfolio
- Position changes always create Transaction records (event sourcing lite)
- Invariants enforced: quantity >= 0, currency consistency

#### Transaction Ledger (Event Store)
```
Transaction
  |-- txn_id, portfolio_id, security_id
  |-- txn_type (BUY, SELL, DEPOSIT, WITHDRAW, FEE, DIVIDEND, COUPON)
  |-- quantity, price, fees
  |-- event_ts
```
- Append-only ledger - no updates or deletes
- Source of truth for position history
- Position table is a materialized projection of ledger state

#### Security Registry Aggregate
```
SecurityRegistry (root)
  |-- security_id, asset_type, currency, display_name
  |
  +-- SecurityIdentifier[] (within aggregate)
  |     |-- id_type (TICKER, CUSIP, ISIN), id_value, is_primary
  |
  +-- EquityDetails (optional, for EQUITY/ETF)
  |     |-- ticker, exchange, country, sector, industry
  |
  +-- BondDetails (optional, for BOND)
        |-- issuer_name, coupon_type, coupon_rate
        |-- maturity_date, par_value, payment_frequency
```
- Shared across all users (reference data)
- Supports multiple identifier types per security
- Asset type determines which detail record exists

#### Simulation Aggregate
```
Simulation (root)
  |-- id, portfolio_id, name
  |-- Request params: horizon_years, num_paths, model_type, scenario
  |-- Results: metrics (dict), sample_paths (list)
  |-- created_at
```
- Persisted simulation results for replay/comparison
- References portfolio but does not modify it
- Compute-intensive - offloaded to simulation package

#### RiskAnalysis Aggregate
```
RiskAnalysis (root)
  |-- id, portfolio_id
  |-- risks (list of identified risks)
  |-- macro_climate_summary
  |-- model_used, created_at
```
- LLM-generated risk assessments
- Snapshot of analysis at a point in time

---

### 2. Market Analytics Context (OLAP)

#### Dimension Tables

| Table | Description |
|-------|-------------|
| `dim_security` | Unified security dimension with equity/bond attributes |
| `dim_funds` | Fund metadata (name, asset_class, expense_ratio) |
| `dim_ticker_tracker` | User-added tickers |
| `dim_asset_classes` | Asset class taxonomy |

#### Fact Tables

| Table | Description |
|-------|-------------|
| `fact_price_daily` | Daily prices for all securities (market + derived bond prices) |
| `fact_position_daily` | Daily position snapshots per portfolio |
| `fact_portfolio_value_daily` | Aggregated portfolio value over time |
| `fact_bond_valuation_daily` | Bond clean prices derived from yield curve |
| `fct_performance` | Performance metrics (returns, volatility, sharpe) |

#### Simulation Parameter Tables

| Table | Description |
|-------|-------------|
| `security_historical_mu` | Historical mean return per security |
| `security_forward_mu` | Forward-looking expected return (analyst targets) |
| `security_volatility` | Annualized volatility per security |

---

## Context Interactions

### Data Flow Diagram

```
                    OLTP                                    OLAP
              (Postgres + API)                        (dbt + DuckDB + S3)

[User Actions]                                      [External Data Sources]
      |                                                      |
      v                                                      v
+------------------+                               +------------------+
| Portfolio        |                               | Ingestion        |
| Management       |                               | Scripts          |
|                  |                               |                  |
| - Portfolios     |    pg_* tables               | - Yahoo Finance  |
| - Positions      | ------------------->          | - FRED           |
| - Transactions   |    (replicated to S3)        | - Price feeds    |
| - Securities     |                               +--------+---------+
+--------+---------+                                        |
         |                                                  v
         |                                         +------------------+
         |                                         | dbt Transform    |
         |                                         |                  |
         |                                         | staging -> int   |
         |                                         | -> marts         |
         +------------------+                      +--------+---------+
                            |                               |
                            |      Analytics Ports          |
                            |      (read-only)              |
                            v                               v
                    +-------+-------+---------------+-------+
                    |               |               |
            AnalyticsRepository   SimulationParamsRepository
                    |               |
                    v               v
              +-----+---------------+-----+
              |    Domain Services        |
              |                           |
              | - PortfolioService        |
              | - SimulationService       |
              | - RiskAnalysisService     |
              +---------------------------+
```

### Anti-Corruption Layer

The OLTP domain does not directly query OLAP tables. Instead, ports define the contract:

**AnalyticsRepository** (port for read-only OLAP access):
- `get_performance_for_tickers()` -> `TickerPerformance`
- `get_fund_metadata_for_tickers()` -> `FundMetadata`
- `get_ticker_details()` -> `TickerDetails`
- `get_price_for_date()` -> `TickerPriceAtDate`

**SimulationParamsRepository** (port for simulation parameters):
- `get_security_params()` -> `SecuritySimParams` (mu, volatility)
- `get_historical_returns()` -> daily returns arrays for correlation

These ports use **value objects** (not domain entities) to transfer data across the boundary, preventing OLAP schema changes from leaking into domain logic.

---

## Aggregate Boundaries & Rules

### Portfolio Aggregate Rules

1. **Transaction sourcing**: Every position change MUST create a Transaction
2. **Consistency**: Position.quantity = sum(BUY quantities) - sum(SELL quantities)
3. **Average cost**: Recalculated on each BUY using weighted average
4. **Deletion**: Selling entire position creates SELL transaction then deletes Position

### Security Registry Rules

1. **Shared reference data**: Securities are not owned by portfolios
2. **Auto-creation**: Holdings can trigger security creation if not found
3. **Identifier flexibility**: Same security can have ticker + CUSIP + ISIN

### Cross-Aggregate Operations

Operations spanning aggregates use **Commands**:

```
CreatePortfolioWithHoldingsCommand
  |-- Creates Portfolio (aggregate 1)
  |-- Creates Securities if needed (aggregate 2)
  |-- Creates Positions (within Portfolio aggregate)
  |-- Creates Transactions (event store)
  |-- Uses UnitOfWork for atomicity
```

Commands coordinate multiple repositories within a single database transaction.

---

## OLTP vs OLAP Responsibilities

| Concern | OLTP (api/) | OLAP (dbt/) |
|---------|-------------|-------------|
| Current positions | Source of truth | Replicated snapshot |
| Transaction history | Source of truth | Replicated for audit |
| Security metadata | Source of truth | Denormalized for queries |
| Price history | N/A | Source of truth |
| Performance metrics | N/A | Computed & stored |
| Simulation params | Fetches via port | Computes mu, vol, correlation |
| User authentication | Source of truth | N/A |

---

## Data Replication

### Postgres to OLAP (CDC-lite)

The `replicate_postgres_to_duckdb.py` script exports OLTP tables to S3:

```
pg_portfolio         -> s3://bucket/data/raw/pg_portfolio.parquet
pg_security_registry -> s3://bucket/data/raw/pg_security_registry.parquet
pg_position_current  -> s3://bucket/data/raw/pg_position_current.parquet
pg_transaction_ledger-> s3://bucket/data/raw/pg_transaction_ledger.parquet
...
```

dbt reads these as external sources and joins with market data to produce marts.

### Refresh Cadence

- **Market data ingestion**: Daily (prices, yields)
- **Postgres replication**: On-demand or scheduled
- **dbt run**: After ingestion completes
- **API reads marts**: Real-time (query on demand)

---

## Value Objects

Value objects represent data crossing context boundaries without identity:

```python
# Analytics value objects
TickerPerformance    # Performance metrics from OLAP
FundMetadata         # Fund info from OLAP
TickerDetails        # Enriched ticker data for UI
TickerPriceAtDate    # Price lookup result

# Simulation value objects
SecuritySimParams    # mu, volatility per security
HistoricalReturns    # Daily returns for correlation

# OAuth value objects
OAuthTokens          # Tokens from OAuth provider
OAuthUserInfo        # User info from ID token
```

These are immutable (frozen dataclasses or Pydantic models with `frozen=True`).

---

## Key Design Decisions

1. **Event sourcing lite**: Transaction ledger is append-only, Position is derived
2. **CQRS separation**: OLTP handles commands, OLAP handles complex queries
3. **Ports for analytics**: OLTP domain never imports OLAP schemas directly
4. **S3 as interchange**: Both systems read/write Parquet on S3
5. **DuckDB ephemeral**: OLAP compute is stateless; state lives in S3
6. **No ORM in domain**: Direct SQL in adapters preserves domain purity
