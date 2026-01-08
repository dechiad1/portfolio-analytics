"""
Script to fetch benchmark data (S&P 500, risk-free rate)
"""

import yfinance as yf
import pandas as pd
import duckdb
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from config import START_DATE, END_DATE, BENCHMARK_TICKER, RISK_FREE_RATE, get_db_path

def fetch_benchmark_prices(benchmark_ticker, start_date, end_date):
    """
    Fetch benchmark (S&P 500) price data
    
    Args:
        benchmark_ticker: Ticker symbol for benchmark
        start_date: Start date
        end_date: End date
    
    Returns:
        DataFrame with date and benchmark_price
    """
    print(f"\n📈 Fetching benchmark data ({benchmark_ticker})...")
    
    data = yf.download(
        benchmark_ticker,
        start=start_date,
        end=end_date,
        progress=False,
        auto_adjust=True
    )
    
    if data.empty:
        raise ValueError(f"No data available for benchmark {benchmark_ticker}")

    # Reset index to make date a column
    data = data.reset_index()

    # Flatten the Close column if it's multidimensional
    close_values = data['Close'].squeeze() if hasattr(data['Close'], 'squeeze') else data['Close']

    df = pd.DataFrame({
        'date': data['Date'],
        'benchmark_ticker': benchmark_ticker,
        'benchmark_price': close_values
    })
    
    print(f"✓ Fetched {len(df)} days of benchmark data")
    return df

def create_risk_free_rate_data(start_date, end_date, rate):
    """
    Create daily risk-free rate data
    
    In a production system, you'd fetch this from FRED API.
    For simplicity, we'll use a constant rate.
    
    Args:
        start_date: Start date
        end_date: End date  
        rate: Annual risk-free rate (e.g., 0.03 for 3%)
    
    Returns:
        DataFrame with date and risk_free_rate
    """
    print(f"\n📊 Creating risk-free rate data ({rate*100}% annual)...")
    
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Convert annual rate to daily
    daily_rate = rate / 365
    
    df = pd.DataFrame({
        'date': dates,
        'risk_free_rate': rate,  # Keep as annual for easier calculations
        'risk_free_rate_daily': daily_rate
    })
    
    print(f"✓ Created {len(df)} days of risk-free rate data")
    return df

def load_to_duckdb(benchmark_df, rfr_df):
    """
    Load benchmark and risk-free rate data to DuckDB
    
    Args:
        benchmark_df: Benchmark prices DataFrame
        rfr_df: Risk-free rate DataFrame
    """
    print(f"\n💾 Loading benchmark data to DuckDB...")
    
    db_path = get_db_path()
    con = duckdb.connect(db_path)
    
    # Load benchmark prices
    con.execute("DROP TABLE IF EXISTS raw_benchmark_prices")
    con.execute("CREATE TABLE raw_benchmark_prices AS SELECT * FROM benchmark_df")
    
    benchmark_count = con.execute("SELECT COUNT(*) FROM raw_benchmark_prices").fetchone()[0]
    print(f"✓ Loaded {benchmark_count:,} benchmark records")
    
    # Load risk-free rates
    con.execute("DROP TABLE IF EXISTS raw_risk_free_rates")
    con.execute("CREATE TABLE raw_risk_free_rates AS SELECT * FROM rfr_df")
    
    rfr_count = con.execute("SELECT COUNT(*) FROM raw_risk_free_rates").fetchone()[0]
    print(f"✓ Loaded {rfr_count:,} risk-free rate records")
    
    # Show sample
    print("\nSample benchmark data:")
    sample = con.execute("SELECT * FROM raw_benchmark_prices LIMIT 5").df()
    print(sample.to_string(index=False))
    
    con.close()

def main():
    """Main execution function"""
    try:
        print("=" * 60)
        print("BENCHMARK DATA INGESTION")
        print("=" * 60)
        
        # Fetch benchmark prices
        benchmark_df = fetch_benchmark_prices(BENCHMARK_TICKER, START_DATE, END_DATE)
        
        # Create risk-free rate data
        rfr_df = create_risk_free_rate_data(START_DATE, END_DATE, RISK_FREE_RATE)
        
        # Load to database
        load_to_duckdb(benchmark_df, rfr_df)
        
        print("\n" + "=" * 60)
        print("✓ SUCCESS: Benchmark data ingestion complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: cd dbt && dbt seed")
        print("2. Run: cd dbt && dbt run")
        print("3. View: streamlit run app.py")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
