"""
Script to fetch historical price data for portfolio holdings using yfinance
"""

import yfinance as yf
import pandas as pd
import duckdb
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent))
from config import START_DATE, END_DATE, TICKERS, get_db_path

def fetch_prices(tickers, start_date, end_date):
    """
    Fetch historical adjusted close prices for given tickers
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        DataFrame with columns: date, ticker, price, volume
    """
    print(f"\n📊 Fetching price data for {len(tickers)} tickers...")
    print(f"Date range: {start_date} to {end_date}")
    print("-" * 60)
    
    all_data = []
    
    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] Fetching {ticker}...", end=" ")
            
            # Download data from Yahoo Finance
            data = yf.download(
                ticker, 
                start=start_date, 
                end=end_date,
                progress=False,
                auto_adjust=True  # Use adjusted prices
            )
            
            if data.empty:
                print("❌ No data available")
                continue

            # Reset index to make date a column
            data = data.reset_index()

            # Flatten column names if multi-level (happens with single ticker downloads)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # Prepare dataframe
            df = pd.DataFrame({
                'date': pd.to_datetime(data['Date']),
                'ticker': ticker,
                'open': data['Open'],
                'high': data['High'],
                'low': data['Low'],
                'close': data['Close'],
                'volume': data['Volume']
            })
            
            all_data.append(df)
            print(f"✓ Got {len(df)} days of data")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            continue
    
    if not all_data:
        raise ValueError("No data was successfully fetched for any ticker")
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print("-" * 60)
    print(f"✓ Successfully fetched data for {len(all_data)} / {len(tickers)} tickers")
    print(f"Total records: {len(combined_df):,}")
    
    return combined_df

def load_to_duckdb(df, table_name='raw_prices'):
    """
    Load dataframe into DuckDB database
    
    Args:
        df: DataFrame to load
        table_name: Name of the table to create/replace
    """
    print(f"\n💾 Loading data to DuckDB...")
    
    db_path = get_db_path()
    print(f"Database: {db_path}")
    
    # Connect to DuckDB
    con = duckdb.connect(db_path)
    
    # Drop table if exists and create new one
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
    
    # Verify the data
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"✓ Loaded {count:,} records to table '{table_name}'")
    
    # Show sample
    print("\nSample data:")
    sample = con.execute(f"SELECT * FROM {table_name} LIMIT 5").df()
    print(sample.to_string(index=False))
    
    con.close()

def main():
    """Main execution function"""
    try:
        print("=" * 60)
        print("PORTFOLIO PRICE DATA INGESTION")
        print("=" * 60)
        
        # Fetch prices
        prices_df = fetch_prices(TICKERS, START_DATE, END_DATE)
        
        # Load to database
        load_to_duckdb(prices_df, 'raw_prices')
        
        print("\n" + "=" * 60)
        print("✓ SUCCESS: Price data ingestion complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: python scripts/ingest_benchmarks.py")
        print("2. Run: cd dbt && dbt seed && dbt run")
        print("3. View: streamlit run app.py")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
