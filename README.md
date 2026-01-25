# Portfolio Analytics Platform

A modern data stack project for analyzing investment portfolio performance, risk metrics, and benchmarking.

## Setup

### Prerequisites
- Docker Desktop
- Python 3.11+ with Poetry
- Node.js 18+
- Task (`brew install go-task/tap/go-task`)

### Quick Start
1. `task docker:up` - Start PostgreSQL
2. `task db:migrate` - Run database migrations
3. `task db:seed` - Seed securities data
4. `task run:api` - Start API server (port 8001)
5. `cd web && npm install && npm run dev` - Start frontend (port 5173)

### Full Data Setup (for analytics)
`task setup` - Complete setup including price data fetch and dbt transformations

### Data Refresh
`task refresh` - Fetches latest price data and rebuilds analytical tables

---

## Transactional Tables (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email, password_hash, is_admin) |
| `portfolio` | User portfolios (name, base_currency, FK to users) |
| `security_registry` | Canonical security identity (asset_type: EQUITY/ETF/BOND/CASH, currency, display_name) |
| `security_identifier` | Multiple identifiers per security (TICKER, CUSIP, ISIN with source tracking) |
| `equity_details` | Equity/ETF details (ticker, exchange, sector, industry) |
| `bond_details` | Bond details (issuer, coupon_type, coupon_rate, maturity_date, payment_frequency) |
| `transaction_ledger` | Append-only trade history (BUY, SELL, DEPOSIT, WITHDRAW, DIVIDEND, COUPON, FEE) |
| `position_current` | Materialized current positions (portfolio_id, security_id, quantity, avg_cost) |
| `cash_balance` | Cash balance per portfolio per currency |

---

## Analytical Tables (DuckDB via dbt)

| Table | Purpose |
|-------|---------|
| `dim_ticker_tracker` | Unified ticker list combining seed file + PostgreSQL portfolios |
| `dim_funds` | Comprehensive security dimension with metadata + performance metrics |
| `fct_performance` | Performance calculations (1Y/5Y returns, volatility, Sharpe ratio, benchmark comparison) |
| `fact_price_daily` | Daily prices for all securities (equities from yfinance, bonds from Treasury yields) |
| `dim_security` | Security master replicated from PostgreSQL |

Data flow: PostgreSQL -> replicate -> DuckDB staging -> dbt transformations -> marts

---

## Domain Entities & Holding Relationship

**User** (`api/domain/models/user.py`)
- id, email, password_hash, is_admin, created_at

**Portfolio** (`api/domain/models/portfolio.py`)
- id, user_id, name, base_currency, created_at, updated_at

**Holding** (`api/domain/models/holding.py`)
- A read model combining data from multiple transactional tables:
  - `position_current.quantity` and `position_current.avg_cost`
  - `security_registry.display_name` and `asset_type`
  - `equity_details.ticker`, `sector`, `industry`
  - Current price from DuckDB `dim_funds` mart

Holding is not a single table - it's assembled by joining:
```
position_current + security_registry + equity_details + dim_funds(price)
```

---

## User Journeys

**1. View Securities List** (Securities Page)
- Source: DuckDB `dim_funds` mart
- Shows: ticker, name, asset_class, 1Y/5Y returns, volatility, Sharpe ratio
- API: `GET /analytics/securities`

**2. Track New Ticker**
- Flow: User enters ticker -> yfinance validates -> PostgreSQL insert (security_registry + equity_details)
- API: `POST /tickers/track`
- Note: Run `task refresh` to fetch price data for new tickers

**3. View Portfolio Holdings** (Portfolio Detail Page)
- Source: PostgreSQL position_current + DuckDB price data
- Shows: ticker, quantity, avg_cost, current_price, market_value, gain/loss
- API: `GET /portfolios/{id}/holdings`

**4. Add Holding to Portfolio**
- Flow: User selects ticker from search -> auto-populates sector/price -> saves to position_current
- Source for auto-populate: `GET /analytics/tickers/{ticker}/details` (DuckDB)
- API: `POST /portfolios/{id}/holdings`

**5. Historical Price Lookup**
- When purchase date changes, fetches historical price
- API: `GET /analytics/tickers/{ticker}/price?date=YYYY-MM-DD`
