"""
Script to fetch Treasury yield curve data from FRED API.

This data is used to derive theoretical bond prices for Treasury securities.

FRED Series IDs:
- DGS2: 2-Year Treasury Constant Maturity Rate
- DGS5: 5-Year Treasury Constant Maturity Rate
- DGS10: 10-Year Treasury Constant Maturity Rate
- DGS30: 30-Year Treasury Constant Maturity Rate
"""

import sys
from pathlib import Path

import pandas as pd

try:
    from fredapi import Fred
except ImportError:
    print("Error: fredapi not installed. Run: pip install fredapi")
    sys.exit(1)

sys.path.append(str(Path(__file__).parent))
from config import START_DATE, END_DATE, FRED_API_KEY, get_storage


# Treasury yield series from FRED
TREASURY_SERIES = {
    "DGS2": "2Y",
    "DGS5": "5Y",
    "DGS10": "10Y",
    "DGS30": "30Y",
}


def fetch_treasury_yields(api_key: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch Treasury yield curve data from FRED.

    Args:
        api_key: FRED API key
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format

    Returns:
        DataFrame with columns: date, tenor, yield_rate
    """
    if not api_key:
        raise ValueError(
            "FRED API key not set. Get one free at: "
            "https://fred.stlouisfed.org/docs/api/api_key.html\n"
            "Then set: export FRED_API_KEY=your_key"
        )

    print(f"\n Fetching Treasury yields from FRED...")
    print(f"Date range: {start_date} to {end_date}")
    print("-" * 60)

    fred = Fred(api_key=api_key)
    all_data = []

    for series_id, tenor in TREASURY_SERIES.items():
        try:
            print(f"Fetching {tenor} ({series_id})...", end=" ")

            # Fetch series data
            series = fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date,
            )

            if series.empty:
                print("No data")
                continue

            # Convert to DataFrame
            df = pd.DataFrame(
                {
                    "date": series.index,
                    "tenor": tenor,
                    "yield_rate": series.values / 100,  # Convert % to decimal
                }
            )

            # Drop NaN values (FRED returns NaN for non-trading days)
            df = df.dropna(subset=["yield_rate"])

            all_data.append(df)
            print(f"Got {len(df)} days")

        except Exception as e:
            print(f"Error: {e}")
            continue

    if not all_data:
        raise ValueError("No Treasury yield data was fetched")

    combined = pd.concat(all_data, ignore_index=True)

    print("-" * 60)
    print(f"Fetched {len(combined):,} total yield observations")

    return combined


def load_to_storage(df: pd.DataFrame, table_name: str = "raw_treasury_yields"):
    """
    Load Treasury yields to storage (DuckDB or S3).

    Args:
        df: DataFrame with yield data
        table_name: Target table name
    """
    print(f"\n Loading Treasury yields to storage...")

    storage = get_storage()
    storage.write_table(df, table_name)

    # Show sample
    print("\nSample data:")
    print(df.tail(8).to_string(index=False))


def main():
    """Main execution function."""
    try:
        print("=" * 60)
        print("TREASURY YIELD DATA INGESTION (FRED)")
        print("=" * 60)

        # Fetch yields
        yields_df = fetch_treasury_yields(FRED_API_KEY, START_DATE, END_DATE)

        # Load to storage
        load_to_storage(yields_df)

        print("\n" + "=" * 60)
        print("SUCCESS: Treasury yield ingestion complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
