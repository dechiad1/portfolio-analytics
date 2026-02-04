"""
Configuration file for portfolio analytics project
"""

import os
import csv
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .storage import Storage

# ============================================================================
# DATA INGESTION SETTINGS
# ============================================================================

# Date range for historical data
START_DATE = '2019-01-01'  # 7 years of history for 5Y calculations
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

# Holdings CSV path (fallback if DuckDB table doesn't exist)
HOLDINGS_CSV_PATH = os.path.join(os.path.dirname(__file__), 'holdings.csv')


def get_db_path():
    """Get absolute path to DuckDB database"""
    return os.path.abspath(DB_PATH)


def load_tickers_from_duckdb():
    """
    Load ticker symbols from DuckDB dim_ticker_tracker table.
    This table is managed by dbt and combines:
    - Manually curated seed tickers
    - User portfolio tickers (from PostgreSQL replication)

    Returns:
        List of ticker symbols, or None if table doesn't exist
    """
    try:
        import duckdb
        db_path = get_db_path()

        if not Path(db_path).exists():
            return None

        con = duckdb.connect(db_path, read_only=True)
        try:
            result = con.execute("""
                SELECT ticker
                FROM main_marts.dim_ticker_tracker
                ORDER BY ticker
            """).fetchall()
            tickers = [row[0] for row in result if row[0]]
            con.close()
            return tickers if tickers else None
        except duckdb.CatalogException:
            # Table doesn't exist yet (dbt hasn't run)
            con.close()
            return None
    except ImportError:
        # duckdb not installed
        return None
    except Exception:
        return None


def load_tickers_from_csv():
    """
    Load ticker symbols from holdings.csv (fallback method).

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


def load_tickers():
    """
    Load ticker symbols from the best available source.

    Priority:
    1. DuckDB dim_ticker_tracker (managed by dbt, includes portfolio tickers)
    2. CSV file (fallback for bootstrapping)

    Returns:
        List of ticker symbols
    """
    # Try DuckDB first (preferred - includes user portfolio tickers)
    tickers = load_tickers_from_duckdb()
    if tickers:
        return tickers

    # Fall back to CSV (for bootstrapping before dbt runs)
    return load_tickers_from_csv()


# List of tickers to track
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

def validate_config():
    """Validate configuration settings"""
    errors = []

    if not START_DATE:
        errors.append("START_DATE must be set")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return True

def get_ticker_source():
    """Return which source tickers are loaded from."""
    tickers = load_tickers_from_duckdb()
    if tickers:
        return "DuckDB (dim_ticker_tracker)"
    return "CSV (holdings.csv)"


def get_storage(force_local: bool = False) -> "Storage":
    """
    Get the appropriate storage backend based on configuration.

    Args:
        force_local: If True, always use local DuckDB storage.

    Returns:
        Storage instance (LocalDuckDBStorage or S3ParquetStorage).
    """
    try:
        from .storage import get_storage as _get_storage
    except ImportError:
        from storage import get_storage as _get_storage
    return _get_storage(force_local=force_local)


if __name__ == "__main__":
    print("Portfolio Analytics Configuration")
    print("=" * 50)
    print(f"Start Date: {START_DATE}")
    print(f"End Date: {END_DATE}")
    print(f"Risk-Free Rate: Sourced from FRED (10Y Treasury)")
    print(f"Database Path: {get_db_path()}")
    print(f"Benchmark: {BENCHMARK_TICKER}")
    print(f"Ticker Source: {get_ticker_source()}")
    print(f"Number of Tickers: {len(TICKERS)}")
    print(f"Tickers: {', '.join(TICKERS[:10])}{'...' if len(TICKERS) > 10 else ''}")
    print("=" * 50)

    try:
        validate_config()
        print("Configuration is valid")
    except ValueError as e:
        print(f"Configuration error: {e}")
