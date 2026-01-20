"""
Configuration file for portfolio analytics project
"""

import os
import csv
from datetime import datetime
from pathlib import Path

# ============================================================================
# DATA INGESTION SETTINGS
# ============================================================================

# Date range for historical data
START_DATE = '2022-01-01'  # Adjust to your investment start date
END_DATE = datetime.now().strftime('%Y-%m-%d')  # Today

# Note: Risk-free rate is now sourced from FRED Treasury yields (10Y)
# See ingest_treasury_yields.py and stg_risk_free_rates.sql

# ============================================================================
# DATABASE SETTINGS
# ============================================================================

# DuckDB database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'portfolio.duckdb')

# ============================================================================
# API SETTINGS (Optional)
# ============================================================================

# Alpha Vantage API key (free tier: 25 calls/day)
# Sign up at: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')

# FRED API key (free, unlimited)
# Sign up at: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.getenv('FRED_API_KEY', '')

# ============================================================================
# PORTFOLIO SETTINGS
# ============================================================================

# Benchmark ticker (for comparison)
BENCHMARK_TICKER = 'VFIAX'  # S&P 500 index fund

# Holdings CSV path
HOLDINGS_CSV_PATH = os.path.join(os.path.dirname(__file__), 'holdings.csv')

def load_tickers():
    """
    Load ticker symbols from holdings.csv

    Returns:
        List of ticker symbols
    """
    tickers = []
    holdings_path = Path(HOLDINGS_CSV_PATH)

    if not holdings_path.exists():
        raise FileNotFoundError(
            f"Holdings file not found at {HOLDINGS_CSV_PATH}. "
            "Please create a holdings.csv file with a 'ticker' column."
        )

    with open(holdings_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'ticker' in row and row['ticker'].strip():
                tickers.append(row['ticker'].strip())

    if not tickers:
        raise ValueError("No tickers found in holdings.csv")

    return tickers

# List of tickers to track (loaded from holdings.csv)
TICKERS = load_tickers()

# ============================================================================
# CALCULATION SETTINGS
# ============================================================================

# Frequency for return calculations
RETURN_FREQUENCY = 'monthly'  # 'daily', 'weekly', or 'monthly'

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db_path():
    """Get absolute path to DuckDB database"""
    return os.path.abspath(DB_PATH)

def validate_config():
    """Validate configuration settings"""
    errors = []

    if not START_DATE:
        errors.append("START_DATE must be set")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return True

if __name__ == "__main__":
    print("Portfolio Analytics Configuration")
    print("=" * 50)
    print(f"Start Date: {START_DATE}")
    print(f"End Date: {END_DATE}")
    print(f"Risk-Free Rate: Sourced from FRED (10Y Treasury)")
    print(f"Database Path: {get_db_path()}")
    print(f"Benchmark: {BENCHMARK_TICKER}")
    print(f"Number of Holdings: {len(TICKERS)}")
    print("=" * 50)

    try:
        validate_config()
        print("✓ Configuration is valid")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
