"""
Script to fetch fund metadata using yfinance
Run this less frequently than price data (weekly/monthly)
"""

import yfinance as yf
import pandas as pd
import duckdb
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from config import TICKERS, get_db_path

def fetch_fund_metadata(tickers):
    """
    Fetch fund metadata from Yahoo Finance for given tickers

    Args:
        tickers: List of ticker symbols

    Returns:
        DataFrame with fund metadata
    """
    print(f"\n📊 Fetching fund metadata for {len(tickers)} tickers...")
    print("-" * 60)

    metadata_list = []

    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] Fetching {ticker}...", end=" ")

            # Create Ticker object
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            # Extract metadata (with fallbacks for missing data)
            metadata = {
                'ticker': ticker,
                'fund_name': info.get('longName') or info.get('shortName') or ticker,
                'expense_ratio': info.get('annualReportExpenseRatio'),
                'fund_family': info.get('fundFamily'),
                'category': info.get('category'),
                'fund_inception_date': info.get('fundInceptionDate'),
                'total_assets': info.get('totalAssets'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange'),
                'quote_type': info.get('quoteType'),
                'long_business_summary': info.get('longBusinessSummary'),
            }

            # Try to get fund-specific data (ETFs/Mutual Funds)
            try:
                funds_data = ticker_obj.funds_data

                # Asset allocation
                if hasattr(funds_data, 'asset_classes') and funds_data.asset_classes is not None:
                    asset_classes_df = funds_data.asset_classes
                    if not asset_classes_df.empty:
                        # Convert to readable format
                        allocations = []
                        for _, row in asset_classes_df.iterrows():
                            if 'netAssets' in row and row['netAssets'] and row['netAssets'] > 0:
                                allocations.append(f"{row.get('assetClass', 'Unknown')}: {row['netAssets']:.1f}%")
                        metadata['asset_distribution'] = ' | '.join(allocations) if allocations else None
                    else:
                        metadata['asset_distribution'] = None
                else:
                    metadata['asset_distribution'] = None

                # Sector weightings
                if hasattr(funds_data, 'sector_weightings') and funds_data.sector_weightings is not None:
                    sector_df = funds_data.sector_weightings
                    if not sector_df.empty and len(sector_df) > 0:
                        top_sectors = []
                        for _, row in sector_df.head(5).iterrows():
                            if 'weightPercentage' in row and row['weightPercentage']:
                                sector_name = row.get('sectorName', row.get('sector', 'Unknown'))
                                top_sectors.append(f"{sector_name}: {row['weightPercentage']:.1f}%")
                        metadata['top_sectors'] = ' | '.join(top_sectors) if top_sectors else None
                    else:
                        metadata['top_sectors'] = None
                else:
                    metadata['top_sectors'] = None

            except (AttributeError, Exception) as e:
                # Not a fund or data unavailable
                metadata['asset_distribution'] = None
                metadata['top_sectors'] = None

            metadata_list.append(metadata)
            print(f"✓ {metadata['fund_name'][:40]}")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            # Add minimal record on error
            metadata_list.append({
                'ticker': ticker,
                'fund_name': ticker,
                'expense_ratio': None,
                'fund_family': None,
                'category': None,
                'fund_inception_date': None,
                'total_assets': None,
                'currency': 'USD',
                'exchange': None,
                'quote_type': None,
                'long_business_summary': None,
                'asset_distribution': None,
                'top_sectors': None
            })
            continue

    df = pd.DataFrame(metadata_list)

    print("-" * 60)
    print(f"✓ Successfully fetched metadata for {len(df)} / {len(tickers)} tickers")
    print(f"Records with expense ratio: {df['expense_ratio'].notna().sum()}")
    print(f"Records with asset distribution: {df['asset_distribution'].notna().sum()}")

    return df

def load_to_duckdb(df, table_name='raw_fund_metadata'):
    """
    Load fund metadata into DuckDB database

    Args:
        df: DataFrame to load
        table_name: Name of the table to create/replace
    """
    print(f"\n💾 Loading fund metadata to DuckDB...")

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
    sample = con.execute(f"""
        SELECT
            ticker,
            fund_name,
            expense_ratio,
            fund_family,
            category,
            CASE
                WHEN asset_distribution IS NOT NULL AND LENGTH(CAST(asset_distribution AS VARCHAR)) > 50
                THEN SUBSTRING(CAST(asset_distribution AS VARCHAR), 1, 50) || '...'
                ELSE CAST(asset_distribution AS VARCHAR)
            END as asset_distribution_preview
        FROM {table_name}
        LIMIT 5
    """).df()
    print(sample.to_string(index=False))

    # Show data quality stats
    print("\nData Quality Summary:")
    stats = con.execute(f"""
        SELECT
            COUNT(*) as total_records,
            SUM(CASE WHEN expense_ratio IS NOT NULL THEN 1 ELSE 0 END) as has_expense_ratio,
            SUM(CASE WHEN fund_family IS NOT NULL THEN 1 ELSE 0 END) as has_fund_family,
            SUM(CASE WHEN category IS NOT NULL THEN 1 ELSE 0 END) as has_category,
            SUM(CASE WHEN asset_distribution IS NOT NULL THEN 1 ELSE 0 END) as has_asset_dist,
            SUM(CASE WHEN long_business_summary IS NOT NULL THEN 1 ELSE 0 END) as has_description
        FROM {table_name}
    """).df()
    print(stats.to_string(index=False))

    con.close()

def main():
    """Main execution function"""
    try:
        print("=" * 60)
        print("FUND METADATA INGESTION")
        print("=" * 60)
        print("\nThis script fetches fund metadata from Yahoo Finance.")
        print("Run this periodically (weekly/monthly) as metadata changes infrequently.\n")

        # Fetch metadata
        metadata_df = fetch_fund_metadata(TICKERS)

        # Load to database
        load_to_duckdb(metadata_df, 'raw_fund_metadata')

        print("\n" + "=" * 60)
        print("✓ SUCCESS: Fund metadata ingestion complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: cd dbt && dbt run")
        print("2. View: Query raw_fund_metadata table in DuckDB")
        print("\nNote: Some funds may have incomplete metadata from Yahoo Finance.")
        print("You can manually add missing data to the table or supplement with other sources.")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
