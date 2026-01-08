# Portfolio Analytics - Project Overview

## 📦 What's Included

Your zip file contains a complete, production-ready portfolio analytics platform!

## 🗂️ Project Structure

```
portfolio-analytics/
│
├── 📄 README.md              # Comprehensive documentation
├── 📄 QUICKSTART.md          # Get started in 10 minutes
├── 📄 requirements.txt       # Python dependencies
├── 📄 .gitignore            # Git ignore rules
├── 📄 .env.example          # Environment variables template
├── 📄 app.py                # Streamlit dashboard (main app)
│
├── 📁 scripts/               # Data ingestion scripts
│   ├── config.py            # Configuration settings
│   ├── ingest_prices.py     # Fetch price data
│   └── ingest_benchmarks.py # Fetch benchmark data
│
├── 📁 dbt/                  # DBT transformation project
│   ├── dbt_project.yml      # DBT configuration
│   ├── profiles.yml         # Database connection
│   │
│   ├── 📁 seeds/            # Static data
│   │   └── holdings.csv     # Your portfolio holdings
│   │
│   └── 📁 models/           # SQL transformations
│       ├── sources.yml      # Source definitions
│       │
│       ├── 📁 staging/      # Clean raw data
│       │   ├── stg_prices.sql
│       │   ├── stg_holdings.sql
│       │   └── stg_benchmarks.sql
│       │
│       ├── 📁 intermediate/ # Calculate returns
│       │   ├── int_daily_returns.sql
│       │   └── int_monthly_returns.sql
│       │
│       └── 📁 marts/        # Final analytics
│           ├── fct_performance.sql
│           └── dim_asset_classes.sql
│
├── 📁 data/                 # Database storage (created on first run)
│   ├── portfolio.duckdb     # DuckDB database
│   └── raw/                 # Optional raw data backup
│
└── 📁 docs/                 # Additional documentation

```

## 🔄 Data Flow

```
┌─────────────────┐
│  Yahoo Finance  │
│  (Free API)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Python Scripts  │
│ ingest_*.py     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DuckDB       │
│ portfolio.duckdb│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   DBT Models    │
│  Transformations│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Streamlit     │
│   Dashboard     │
└─────────────────┘
```

## 📊 What Gets Built

### 1. Raw Data Tables
- `raw_prices`: Daily OHLCV data for all holdings
- `raw_benchmark_prices`: S&P 500 benchmark data
- `raw_risk_free_rates`: Risk-free rate (Treasury proxy)

### 2. Staging Tables (Clean Data)
- `stg_prices`: Cleaned price data
- `stg_holdings`: Your portfolio holdings
- `stg_benchmarks`: Benchmark and risk-free rates

### 3. Intermediate Tables (Calculations)
- `int_daily_returns`: Daily return calculations
- `int_monthly_returns`: Monthly return calculations

### 4. Marts Tables (Final Analytics)
- `fct_performance`: Performance metrics per holding
  - Total return
  - Annualized return
  - Volatility
  - Sharpe ratio
  - vs. Benchmark
  
- `dim_asset_classes`: Holdings with metadata
  - Asset class categorization
  - Sector information
  - Performance metrics

## 🎨 Dashboard Features

Your Streamlit dashboard includes:

1. **Top Metrics**
   - Average portfolio return
   - Best performer
   - Average Sharpe ratio
   - Holdings beating benchmark

2. **Performance Table**
   - Color-coded returns
   - Sortable columns
   - Benchmark comparison

3. **Risk vs. Return Chart**
   - Interactive scatter plot
   - Sized by Sharpe ratio
   - Color-coded by performance

4. **Asset Class Analysis**
   - Distribution pie chart
   - Average metrics by class
   - Holdings count

5. **Benchmark Comparison**
   - Bar chart showing outperformance
   - Color-coded (green/red)

6. **Price History**
   - Multi-ticker comparison
   - Normalized to base 100
   - Interactive line chart

## 🎯 Key Metrics Calculated

| Metric | Formula | What It Means |
|--------|---------|---------------|
| Total Return | `((End - Start)/ Start) × 100` | Overall gain/loss |
| Annualized Return | `(End/Start)^(1/years) - 1` | Compound annual growth |
| Volatility | `StdDev(returns) × √252` | How much prices swing |
| Sharpe Ratio | `(Return - RFR) / Volatility` | Risk-adjusted return |
| vs. Benchmark | `Your Return - S&P 500 Return` | Relative performance |

## 🔧 Customization Points

Easy places to modify:

1. **Your Holdings**
   - Edit: `dbt/seeds/holdings.csv`
   - Add your actual tickers

2. **Date Range**
   - Edit: `scripts/config.py`
   - Change `START_DATE` and `END_DATE`

3. **Risk-Free Rate**
   - Edit: `scripts/config.py`
   - Adjust `RISK_FREE_RATE`

4. **Benchmark**
   - Edit: `scripts/config.py`
   - Change `BENCHMARK_TICKER`

5. **Dashboard Colors/Layout**
   - Edit: `app.py`
   - Modify Plotly chart settings

## 🚀 Deployment Options

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud (Free)
1. Push to GitHub
2. Connect at share.streamlit.io
3. Deploy in 1 click

### Docker
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "app.py"]
```

## 📚 Learning Path

**Week 1**: Get it working
- Follow QUICKSTART.md
- See your data visualized

**Week 2**: Understand the code
- Read through DBT models
- Understand SQL transformations
- Learn how metrics are calculated

**Week 3**: Extend functionality
- Add new metrics (max drawdown)
- Create correlation matrix
- Build Monte Carlo simulations

**Week 4**: Production-ize
- Schedule daily updates
- Deploy to cloud
- Add email alerts

## 💼 Resume Impact

You can now say:

✅ "Built automated portfolio analytics platform using modern data stack"
✅ "Implemented ETL pipeline with Python, DuckDB, and DBT"
✅ "Created interactive dashboards with Streamlit and Plotly"
✅ "Applied financial concepts: Sharpe ratio, volatility, benchmarking"
✅ "Demonstrated data engineering and analytics skills"

## 🎓 Tech Stack Highlights

- **Python**: Data engineering language
- **DuckDB**: Modern embedded analytics database
- **DBT**: Industry-standard transformation framework
- **Streamlit**: Fast dashboard prototyping
- **Plotly**: Interactive visualizations
- **SQL**: Data transformation and analysis

## 📞 Support

If you get stuck:
1. Check QUICKSTART.md
2. Read code comments
3. Review error messages carefully
4. Check DBT/Streamlit documentation

## 🎉 Have Fun!

This is a real, production-quality project you can:
- Put on your resume
- Show in interviews  
- Use for your actual investments
- Extend with new features
- Deploy for friends/family

Happy coding! 📊
