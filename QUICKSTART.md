# Quick Start Guide

## 🚀 Get Up and Running in 10 Minutes

### Step 1: Extract the Project

```bash
# Extract the zip file
unzip portfolio-analytics.zip
cd portfolio-analytics
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies (this will take a few minutes)
pip install -r requirements.txt
```

### Step 3: Fetch Your Data

```bash
# Fetch historical prices (this will take 2-3 minutes)
python scripts/ingest_prices.py

# Fetch benchmark data
python scripts/ingest_benchmarks.py
```

**Expected output:**
```
📊 Fetching price data for 17 tickers...
[1/17] Fetching MJGXX... ✓ Got 945 days of data
[2/17] Fetching JPM... ✓ Got 945 days of data
...
✓ Successfully fetched data for 17 / 17 tickers
```

### Step 4: Transform Data with DBT

```bash
# Navigate to dbt directory
cd dbt

# Load your holdings into the database
dbt seed

# Run all transformations
dbt run

# (Optional) Run tests
dbt test
```

**Expected output:**
```
Running with dbt=1.7.0
Found 6 models, 0 tests, 0 snapshots...

Completed successfully

Done. PASS=6 WARN=0 ERROR=0 SKIP=0 TOTAL=6
```

### Step 5: Launch Dashboard

```bash
# Go back to project root
cd ..

# Launch Streamlit dashboard
streamlit run app.py
```

Your browser should automatically open to `http://localhost:8501`

---

## 🎉 You're Done!

You should now see:
- Performance metrics for all holdings
- Risk vs. return scatter plot
- Asset class distribution
- Benchmark comparison charts
- Interactive price history

---

## 🔍 What Just Happened?

1. **Python scripts** fetched real market data from Yahoo Finance
2. **DuckDB** stored the data in a local database
3. **DBT** transformed raw data into analytics-ready tables
4. **Streamlit** created an interactive dashboard

---

## 🛠️ Troubleshooting

### "Module not found" error
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### "No data available" for certain tickers
Some tickers (especially money market funds) might not have data in Yahoo Finance.
This is normal - the dashboard will work with whatever data is available.

### DBT connection errors
Make sure you're running `dbt` commands from the `dbt/` directory.

### Dashboard shows "Error loading data"
Make sure you've completed steps 3 and 4 (data ingestion and DBT transformations).

---

## 📝 Next Steps

1. **Customize your holdings**: Edit `dbt/seeds/holdings.csv`
2. **Add more metrics**: Explore DBT models in `dbt/models/`
3. **Schedule updates**: Set up a cron job or GitHub Action
4. **Deploy dashboard**: Use Streamlit Cloud for free hosting

---

## 🎓 Learning Resources

- **DBT Tutorial**: https://docs.getdbt.com/docs/introduction
- **DuckDB Guide**: https://duckdb.org/docs/
- **Streamlit Docs**: https://docs.streamlit.io/

---

## 💬 Need Help?

Check out:
- `README.md` for detailed documentation
- `docs/setup_guide.md` for advanced configuration
- Code comments in Python and SQL files

Happy analyzing! 📊
