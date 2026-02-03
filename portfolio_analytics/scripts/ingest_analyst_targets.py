"""
Script to fetch analyst price targets using yfinance
Run this weekly (analyst targets update infrequently)

Fetches:
- currentPrice
- targetMeanPrice (12-month analyst target)
- targetHighPrice
- targetLowPrice
- numberOfAnalystOpinions
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.append(str(Path(__file__).parent))
from config import TICKERS, get_storage


def fetch_analyst_targets(tickers: list[str]) -> pd.DataFrame:
    """
    Fetch analyst price targets from Yahoo Finance for given tickers.

    Args:
        tickers: List of ticker symbols

    Returns:
        DataFrame with analyst target data
    """
    print(f"\nFetching analyst targets for {len(tickers)} tickers...")
    print("-" * 60)

    targets_list = []
    fetched_at = datetime.now()

    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] Fetching {ticker}...", end=" ")

            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            target_data = {
                "ticker": ticker,
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "target_mean_price": info.get("targetMeanPrice"),
                "target_high_price": info.get("targetHighPrice"),
                "target_low_price": info.get("targetLowPrice"),
                "analyst_count": info.get("numberOfAnalystOpinions", 0),
                "fetched_at": fetched_at,
            }

            # Calculate implied return if we have the data
            if target_data["current_price"] and target_data["target_mean_price"]:
                target_data["implied_return"] = (
                    target_data["target_mean_price"] / target_data["current_price"]
                ) - 1
            else:
                target_data["implied_return"] = None

            targets_list.append(target_data)
            analyst_count = target_data["analyst_count"] or 0
            if target_data["target_mean_price"]:
                print(
                    f"OK - Target: ${target_data['target_mean_price']:.2f} ({analyst_count} analysts)"
                )
            else:
                print("No analyst coverage")

        except Exception as e:
            print(f"Error: {str(e)}")
            targets_list.append(
                {
                    "ticker": ticker,
                    "current_price": None,
                    "target_mean_price": None,
                    "target_high_price": None,
                    "target_low_price": None,
                    "analyst_count": 0,
                    "implied_return": None,
                    "fetched_at": fetched_at,
                }
            )

    df = pd.DataFrame(targets_list)

    print("-" * 60)
    print(f"Fetched data for {len(df)} / {len(tickers)} tickers")
    print(f"Tickers with analyst coverage: {df['target_mean_price'].notna().sum()}")

    return df


def load_to_storage(df: pd.DataFrame, table_name: str = "raw_analyst_targets") -> None:
    """
    Load analyst targets into storage (DuckDB or S3).

    Args:
        df: DataFrame to load
        table_name: Name of the table to create/replace
    """
    print(f"\nLoading analyst targets to storage...")

    storage = get_storage()
    storage.write_table(df, table_name)

    # Show sample
    print("\nSample data (top by implied return):")
    sample = df[df['target_mean_price'].notna()].nlargest(10, 'implied_return')[
        ['ticker', 'current_price', 'target_mean_price', 'analyst_count', 'implied_return']
    ]
    sample['implied_return_pct'] = (sample['implied_return'] * 100).round(2)
    print(sample.drop(columns=['implied_return']).to_string(index=False))

    # Show data quality stats
    print("\nData Quality Summary:")
    print(f"  Total records: {len(df)}")
    print(f"  Has current price: {df['current_price'].notna().sum()}")
    print(f"  Has target price: {df['target_mean_price'].notna().sum()}")
    print(f"  Has analysts: {(df['analyst_count'] > 0).sum()}")
    if df['analyst_count'].notna().any():
        print(f"  Avg analyst count: {df['analyst_count'].mean():.1f}")


def main() -> None:
    """Main execution function."""
    try:
        print("=" * 60)
        print("ANALYST TARGETS INGESTION")
        print("=" * 60)
        print("\nThis script fetches analyst price targets from Yahoo Finance.")
        print("Run this weekly as analyst targets update infrequently.\n")

        # Fetch analyst targets
        targets_df = fetch_analyst_targets(TICKERS)

        # Load to storage
        load_to_storage(targets_df, "raw_analyst_targets")

        print("\n" + "=" * 60)
        print("SUCCESS: Analyst targets ingestion complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: cd dbt && dbt run --select stg_analyst_targets")
        print("2. View: Query raw_analyst_targets table in DuckDB")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
