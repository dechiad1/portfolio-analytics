# System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📡 Yahoo Finance API    📊 FRED API      📈 Alpha Vantage      │
│  (Price Data)           (Macro Data)      (Alternative)          │
│                                                                   │
└────────────┬─────────────────────────────────────┬──────────────┘
             │                                     │
             ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER (Python)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📝 ingest_prices.py     📝 ingest_benchmarks.py                │
│  - Fetch OHLCV data      - Fetch S&P 500                        │
│  - Handle errors         - Fetch risk-free rate                  │
│  - Validate data         - Daily updates                         │
│                                                                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER (DuckDB)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Raw Tables:                                                      │
│  ├── raw_prices              (OHLCV data)                        │
│  ├── raw_benchmark_prices    (S&P 500)                           │
│  └── raw_risk_free_rates     (Treasury rates)                    │
│                                                                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 TRANSFORMATION LAYER (DBT)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Staging (Clean):                                                │
│  ├── stg_prices           → Clean price data                     │
│  ├── stg_holdings         → Portfolio metadata                   │
│  └── stg_benchmarks       → Benchmark data                       │
│                                                                   │
│  Intermediate (Calculate):                                       │
│  ├── int_daily_returns    → Daily % changes                      │
│  └── int_monthly_returns  → Monthly % changes                    │
│                                                                   │
│  Marts (Analytics):                                              │
│  ├── fct_performance      → All metrics per holding             │
│  └── dim_asset_classes    → Holdings + metadata                 │
│                                                                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER (Streamlit)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Dashboard Components:                                           │
│  ├── 📊 Performance Metrics                                      │
│  ├── 📈 Risk vs Return Chart                                     │
│  ├── 🏛️ Asset Class Distribution                                │
│  ├── 📊 Benchmark Comparison                                     │
│  └── 📈 Price History Explorer                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Detail

### 1. **Ingestion** (Python Scripts)
```
User runs: python scripts/ingest_prices.py

Flow:
1. Read tickers from config
2. For each ticker:
   - Call Yahoo Finance API
   - Download historical prices
   - Validate data quality
3. Load into DuckDB raw tables
4. Log success/failures
```

### 2. **Storage** (DuckDB)
```
Database: portfolio.duckdb

Tables created:
- raw_prices (date, ticker, open, high, low, close, volume)
- raw_benchmark_prices (date, ticker, price)
- raw_risk_free_rates (date, rate)
```

### 3. **Transformation** (DBT)
```
User runs: dbt run

Execution order:
1. Staging models (views)
   stg_prices.sql
   stg_holdings.sql
   stg_benchmarks.sql

2. Intermediate models (views)
   int_daily_returns.sql
   int_monthly_returns.sql

3. Marts models (tables)
   fct_performance.sql
   dim_asset_classes.sql

All SQL, versioned, tested
```

### 4. **Visualization** (Streamlit)
```
User runs: streamlit run app.py

Dashboard:
1. Connects to DuckDB
2. Queries mart tables
3. Creates interactive charts
4. Serves at localhost:8501
```

## 📦 Technology Choices & Why

| Component | Technology | Why This Choice |
|-----------|-----------|-----------------|
| **Data Source** | Yahoo Finance (yfinance) | Free, reliable, no API key needed |
| **Ingestion** | Python | Industry standard, great libraries |
| **Database** | DuckDB | Embedded, fast, perfect for analytics |
| **Transform** | DBT | SQL-based, version controlled, testable |
| **Dashboard** | Streamlit | Fast prototyping, Python-native |
| **Viz** | Plotly | Interactive, professional charts |

## 🎯 Design Principles

### 1. **Separation of Concerns**
- **Ingestion**: Only fetches and loads raw data
- **DBT**: Only transforms data
- **Streamlit**: Only visualizes data

### 2. **Idempotency**
- Can re-run any step safely
- DBT models drop/create tables
- Scripts handle existing data

### 3. **Testability**
- DBT includes data quality tests
- Python scripts have error handling
- Database constraints ensure validity

### 4. **Scalability**
- Add new holdings: Edit CSV
- Add new metrics: Add SQL model
- Add new charts: Update Streamlit

### 5. **Version Control Friendly**
- Everything is code (IaC)
- SQL in files, not database
- Configuration in files
- Can track changes in Git

## 🔐 Security Considerations

### Current Implementation
- Local database (no network exposure)
- No authentication required
- Data stored locally

### Production Recommendations
- Use environment variables for API keys
- Add authentication to dashboard
- Encrypt sensitive data
- Use proper database permissions

## 📈 Scaling Paths

### Current: Local Development
```
1 user
Local machine
~20 holdings
Daily updates
```

### Phase 2: Shared Dashboard
```
Small team (2-10 users)
Deploy to Streamlit Cloud
~50 holdings
Hourly updates
Add authentication
```

### Phase 3: Production System
```
Many users (10-100+)
Deploy to cloud (AWS/GCP/Azure)
100s of holdings
Real-time updates
Add caching layer
Add monitoring/alerts
Use production database
```

## 🛠️ Extension Points

Easy places to add functionality:

### 1. New Data Sources
```python
# scripts/ingest_crypto.py
# Fetch cryptocurrency prices
```

### 2. New Metrics
```sql
-- dbt/models/marts/fct_risk_metrics.sql
-- Calculate max drawdown, VaR, etc.
```

### 3. New Visualizations
```python
# app.py
# Add correlation heatmap
# Add Monte Carlo simulation
```

### 4. Alerts
```python
# scripts/alert_volatility.py
# Email when volatility spikes
```

### 5. Automation
```yaml
# .github/workflows/daily_update.yml
# Run data ingestion daily
```

## 💡 Best Practices Implemented

✅ **Configuration Management**: All settings in config files
✅ **Error Handling**: Graceful failures, informative messages
✅ **Documentation**: README, comments, docstrings
✅ **Logging**: Print statements show progress
✅ **Data Quality**: Filters invalid data
✅ **Version Control**: Git-friendly structure
✅ **Reproducibility**: Requirements.txt, clear setup
✅ **Modularity**: Each component independent

## 🎓 Learning Opportunities

This project teaches:

1. **Data Engineering**
   - ETL pipelines
   - Data modeling
   - SQL transformations

2. **Analytics Engineering**
   - DBT framework
   - Data warehousing concepts
   - Business logic in SQL

3. **Financial Analysis**
   - Performance metrics
   - Risk calculations
   - Benchmarking

4. **Software Engineering**
   - Project structure
   - Configuration management
   - Testing and validation

5. **Data Visualization**
   - Dashboard design
   - Interactive charts
   - User experience

## 📊 Example Queries

After setup, you can query directly:

```sql
-- Top 5 performers
SELECT ticker, total_return_pct
FROM fct_performance
ORDER BY total_return_pct DESC
LIMIT 5;

-- Average return by asset class
SELECT asset_class, AVG(total_return_pct) as avg_return
FROM dim_asset_classes
GROUP BY asset_class;

-- Holdings with high risk
SELECT ticker, volatility_pct, sharpe_ratio
FROM fct_performance
WHERE volatility_pct > 20
ORDER BY sharpe_ratio DESC;
```

---

**This architecture is production-quality and interview-ready!** 🚀
