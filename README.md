# Portfolio Analytics Platform

A modern data stack project for analyzing investment portfolio performance, risk metrics, and benchmarking.

## 🎯 What This Project Does

- Fetches historical price data for your investment holdings
- Calculates performance metrics (returns, volatility, Sharpe ratio)
- Compares performance vs. S&P 500 benchmark
- Analyzes asset class distribution
- Generates interactive dashboards

## 🏗️ Architecture

```
Data Sources (APIs) → Python Ingestion → DuckDB → DBT Transformations → Visualizations
```

## 📦 Tech Stack

- **Python**: Data ingestion and orchestration
- **DuckDB**: Embedded analytical database
- **DBT**: SQL-based data transformations
- **Streamlit**: Interactive dashboards (or Evidence.dev)
- **yfinance**: Free financial data API

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Holdings

Edit `dbt/seeds/holdings.csv` with your actual portfolio holdings.

### 3. Fetch Data

```bash
# Fetch historical prices for all holdings
python scripts/ingest_prices.py

# Fetch benchmark data (S&P 500, risk-free rate)
python scripts/ingest_benchmarks.py
```

### 4. Run DBT Transformations

```bash
cd dbt
dbt deps
dbt seed    # Load holdings CSV
dbt run     # Run all transformations
dbt test    # Run data quality tests
```

### 5. View Dashboard

```bash
# Run Streamlit dashboard
streamlit run app.py
```

Open browser to http://localhost:8501

## 📁 Project Structure

```
portfolio-analytics/
├── data/
│   ├── portfolio.duckdb          # DuckDB database (created on first run)
│   └── raw/                       # Raw data files (optional backup)
├── dbt/
│   ├── models/
│   │   ├── staging/               # Clean raw data
│   │   │   ├── stg_prices.sql
│   │   │   ├── stg_holdings.sql
│   │   │   └── stg_benchmarks.sql
│   │   ├── intermediate/          # Calculate returns
│   │   │   ├── int_daily_returns.sql
│   │   │   └── int_monthly_returns.sql
│   │   └── marts/                 # Final analytics tables
│   │       ├── fct_performance.sql
│   │       ├── fct_risk_metrics.sql
│   │       └── dim_asset_classes.sql
│   ├── seeds/
│   │   └── holdings.csv           # Your portfolio holdings
│   ├── tests/
│   │   └── assert_positive_prices.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── scripts/
│   ├── ingest_prices.py           # Fetch price data
│   ├── ingest_benchmarks.py       # Fetch benchmark data
│   └── config.py                  # Configuration
├── docs/
│   └── setup_guide.md             # Detailed setup instructions
├── app.py                         # Streamlit dashboard
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🎓 Learning Path

### Phase 1: Get It Running (Week 1)
1. Follow Quick Start guide
2. Fetch data for your holdings
3. Run DBT models
4. View basic dashboard

### Phase 2: Understand the Code (Week 2)
1. Read through DBT models
2. Understand how returns are calculated
3. Learn Sharpe ratio formula
4. Explore DuckDB database

### Phase 3: Extend It (Week 3+)
1. Add more metrics (max drawdown, correlation)
2. Build Monte Carlo simulations
3. Add email alerts
4. Schedule daily data updates

## 📊 Key Metrics Calculated

- **Total Return**: Percentage gain/loss since investment start
- **Annualized Return**: Compound annual growth rate (CAGR)
- **Volatility**: Standard deviation of returns (annualized)
- **Sharpe Ratio**: Risk-adjusted return metric
- **Benchmark Comparison**: Performance vs. S&P 500
- **Asset Class Distribution**: Portfolio breakdown by type

## 🔧 Configuration

### Edit Your Holdings

`dbt/seeds/holdings.csv`:
```csv
ticker,name,asset_class,sector,broker,purchase_date
JPM,JP Morgan Chase,U.S. Stocks,Financials,Chase,2022-01-15
VFIAX,Vanguard 500 Index,U.S. Stocks,Broad Market,Vanguard,2022-01-15
```

### Adjust Date Ranges

In `scripts/config.py`:
```python
START_DATE = '2022-01-01'  # Your investment start date
END_DATE = '2025-10-27'     # Today or analysis end date
RISK_FREE_RATE = 0.03       # Assumed risk-free rate (3%)
```

## 🐛 Troubleshooting

### yfinance not working?
- Yahoo Finance can be flaky. Try Alpha Vantage instead (requires free API key)
- See `scripts/ingest_prices_alphavantage.py` for alternative

### DuckDB errors?
- Delete `data/portfolio.duckdb` and re-run ingestion
- Make sure DBT profile is configured correctly

### DBT errors?
- Run `dbt debug` to check configuration
- Verify `profiles.yml` is in correct location (`~/.dbt/` or `dbt/`)

## 📚 Resources

### Learning DBT
- [DBT Docs](https://docs.getdbt.com/)
- [DBT Learn](https://courses.getdbt.com/)

### Learning DuckDB
- [DuckDB Docs](https://duckdb.org/docs/)
- [Why DuckDB](https://duckdb.org/why_duckdb)

### Portfolio Theory
- "A Random Walk Down Wall Street" - Burton Malkiel
- Modern Portfolio Theory basics
- Sharpe ratio explained

## 🚀 Next Steps

1. **Automate Updates**: Add GitHub Actions or cron job for daily data refresh
2. **Deploy Dashboard**: Host on Streamlit Cloud or Heroku
3. **Add Features**: Tax-loss harvesting, rebalancing recommendations
4. **Share**: Show to friends, add to resume, demo in interviews

## 🤝 Contributing

This is a learning project! Feel free to:
- Add new metrics
- Improve visualizations
- Add tests
- Share improvements

## 📝 License

MIT License - Feel free to use for learning and portfolio projects

## 💡 Interview Tips

When discussing this project:
- Emphasize **end-to-end ownership** (data → transformations → viz)
- Highlight **modern data stack** knowledge (DBT, DuckDB)
- Discuss **financial concepts** (Sharpe ratio, benchmarking)
- Show **production thinking** (tests, documentation, reproducibility)

---

**Questions? Issues? Want to extend this?** Open an issue or reach out!

Good luck with your portfolio analytics journey! 📈
