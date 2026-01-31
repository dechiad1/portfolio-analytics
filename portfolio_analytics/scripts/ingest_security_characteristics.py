"""
Script to fetch security characteristics for scenario-based LLM selection.

This script fetches fundamental data that helps an LLM understand how securities
might perform under different economic/policy scenarios.

Characteristics captured:
- Market dynamics: beta, volatility, market cap
- Valuation: P/E, forward P/E, P/B, P/S
- Profitability: margins, ROE, ROA
- Income: dividend yield, payout ratio
- Growth: revenue growth, earnings growth
- Financial health: debt/equity, current ratio
- Sector classification: sector, industry

Run this weekly as these metrics change with price movements and quarterly reports.
"""

import sys
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import yfinance as yf

sys.path.append(str(Path(__file__).parent))
from config import TICKERS, get_db_path


def fetch_security_characteristics(tickers: list[str]) -> pd.DataFrame:
    """
    Fetch fundamental characteristics from Yahoo Finance for given tickers.

    Args:
        tickers: List of ticker symbols

    Returns:
        DataFrame with security characteristics
    """
    print(f"\nFetching security characteristics for {len(tickers)} tickers...")
    print("-" * 70)

    characteristics_list = []
    fetched_at = datetime.now()

    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] Fetching {ticker}...", end=" ")

            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            char_data = {
                "ticker": ticker,
                "fetched_at": fetched_at,
                # ============================================================
                # IDENTIFICATION
                # ============================================================
                "security_name": info.get("longName") or info.get("shortName"),
                "quote_type": info.get("quoteType"),  # EQUITY, ETF, etc.
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "exchange": info.get("exchange"),
                "currency": info.get("currency", "USD"),
                # ============================================================
                # MARKET DYNAMICS
                # ============================================================
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "beta": info.get("beta"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "fifty_day_average": info.get("fiftyDayAverage"),
                "two_hundred_day_average": info.get("twoHundredDayAverage"),
                "avg_volume_10d": info.get("averageVolume10days"),
                "avg_volume_3m": info.get("averageVolume"),
                # ============================================================
                # VALUATION METRICS
                # ============================================================
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "enterprise_to_revenue": info.get("enterpriseToRevenue"),
                "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
                # ============================================================
                # PROFITABILITY
                # ============================================================
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "gross_margin": info.get("grossMargins"),
                "ebitda_margin": info.get("ebitdaMargins"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
                # ============================================================
                # INCOME / DIVIDENDS
                # ============================================================
                "dividend_yield": info.get("dividendYield"),
                "dividend_rate": info.get("dividendRate"),
                "trailing_annual_dividend_yield": info.get(
                    "trailingAnnualDividendYield"
                ),
                "payout_ratio": info.get("payoutRatio"),
                "five_year_avg_dividend_yield": info.get("fiveYearAvgDividendYield"),
                "ex_dividend_date": info.get("exDividendDate"),
                # ============================================================
                # GROWTH METRICS
                # ============================================================
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
                "revenue_per_share": info.get("revenuePerShare"),
                # ============================================================
                # FINANCIAL HEALTH
                # ============================================================
                "total_debt": info.get("totalDebt"),
                "total_cash": info.get("totalCash"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "free_cash_flow": info.get("freeCashflow"),
                "operating_cash_flow": info.get("operatingCashflow"),
                # ============================================================
                # SIZE CLASSIFICATION (computed)
                # ============================================================
                "market_cap_category": _classify_market_cap(info.get("marketCap")),
                # ============================================================
                # ETF-SPECIFIC (for ETFs)
                # ============================================================
                "expense_ratio": info.get("annualReportExpenseRatio"),
                "total_assets": info.get("totalAssets"),
                "category": info.get("category"),
                "fund_family": info.get("fundFamily"),
                # ============================================================
                # SCENARIO-RELEVANT CLASSIFICATIONS (computed)
                # ============================================================
                "is_dividend_payer": _is_dividend_payer(info),
                "is_high_growth": _is_high_growth(info),
                "is_value": _is_value(info),
                "is_defensive": _is_defensive_sector(info.get("sector")),
                "is_cyclical": _is_cyclical_sector(info.get("sector")),
                "is_rate_sensitive": _is_rate_sensitive(info),
                "is_inflation_hedge": _is_inflation_hedge(info),
            }

            characteristics_list.append(char_data)

            # Summary output
            beta = char_data.get("beta")
            pe = char_data.get("trailing_pe")
            div_yield = char_data.get("dividend_yield")

            summary_parts = []
            if beta:
                summary_parts.append(f"Beta:{beta:.2f}")
            if pe:
                summary_parts.append(f"P/E:{pe:.1f}")
            if div_yield:
                summary_parts.append(f"Div:{div_yield*100:.1f}%")

            print(f"OK - {' '.join(summary_parts) if summary_parts else 'Basic data'}")

        except Exception as e:
            print(f"Error: {str(e)}")
            characteristics_list.append(
                {
                    "ticker": ticker,
                    "fetched_at": fetched_at,
                    "security_name": None,
                    "quote_type": None,
                    "sector": None,
                    "industry": None,
                    "country": None,
                    "exchange": None,
                    "currency": "USD",
                    "market_cap": None,
                    "enterprise_value": None,
                    "beta": None,
                    "fifty_two_week_high": None,
                    "fifty_two_week_low": None,
                    "fifty_day_average": None,
                    "two_hundred_day_average": None,
                    "avg_volume_10d": None,
                    "avg_volume_3m": None,
                    "trailing_pe": None,
                    "forward_pe": None,
                    "peg_ratio": None,
                    "price_to_book": None,
                    "price_to_sales": None,
                    "enterprise_to_revenue": None,
                    "enterprise_to_ebitda": None,
                    "profit_margin": None,
                    "operating_margin": None,
                    "gross_margin": None,
                    "ebitda_margin": None,
                    "return_on_equity": None,
                    "return_on_assets": None,
                    "dividend_yield": None,
                    "dividend_rate": None,
                    "trailing_annual_dividend_yield": None,
                    "payout_ratio": None,
                    "five_year_avg_dividend_yield": None,
                    "ex_dividend_date": None,
                    "revenue_growth": None,
                    "earnings_growth": None,
                    "earnings_quarterly_growth": None,
                    "revenue_per_share": None,
                    "total_debt": None,
                    "total_cash": None,
                    "debt_to_equity": None,
                    "current_ratio": None,
                    "quick_ratio": None,
                    "free_cash_flow": None,
                    "operating_cash_flow": None,
                    "market_cap_category": None,
                    "expense_ratio": None,
                    "total_assets": None,
                    "category": None,
                    "fund_family": None,
                    "is_dividend_payer": None,
                    "is_high_growth": None,
                    "is_value": None,
                    "is_defensive": None,
                    "is_cyclical": None,
                    "is_rate_sensitive": None,
                    "is_inflation_hedge": None,
                }
            )

    df = pd.DataFrame(characteristics_list)

    print("-" * 70)
    print(f"Fetched data for {len(df)} / {len(tickers)} tickers")
    print(f"With beta: {df['beta'].notna().sum()}")
    print(f"With P/E: {df['trailing_pe'].notna().sum()}")
    print(f"With dividend yield: {df['dividend_yield'].notna().sum()}")

    return df


def _classify_market_cap(market_cap: float | None) -> str | None:
    """Classify market cap into size categories."""
    if market_cap is None:
        return None
    if market_cap >= 200e9:
        return "mega"
    if market_cap >= 10e9:
        return "large"
    if market_cap >= 2e9:
        return "mid"
    if market_cap >= 300e6:
        return "small"
    return "micro"


def _is_dividend_payer(info: dict) -> bool | None:
    """Check if security pays dividends."""
    div_yield = info.get("dividendYield")
    if div_yield is None:
        return None
    return div_yield > 0


def _is_high_growth(info: dict) -> bool | None:
    """Check if security has high growth characteristics."""
    rev_growth = info.get("revenueGrowth")
    if rev_growth is None:
        return None
    return rev_growth > 0.15  # >15% revenue growth


def _is_value(info: dict) -> bool | None:
    """Check if security has value characteristics."""
    pe = info.get("trailingPE")
    pb = info.get("priceToBook")

    if pe is not None and pe > 0 and pe < 15:
        return True
    if pb is not None and pb > 0 and pb < 1.5:
        return True
    if pe is None and pb is None:
        return None
    return False


DEFENSIVE_SECTORS = {
    "Consumer Staples",
    "Healthcare",
    "Utilities",
    "Consumer Defensive",
}

CYCLICAL_SECTORS = {
    "Consumer Discretionary",
    "Consumer Cyclical",
    "Industrials",
    "Materials",
    "Energy",
    "Financial Services",
    "Financials",
}


def _is_defensive_sector(sector: str | None) -> bool | None:
    """Check if security is in a defensive sector."""
    if sector is None:
        return None
    return sector in DEFENSIVE_SECTORS


def _is_cyclical_sector(sector: str | None) -> bool | None:
    """Check if security is in a cyclical sector."""
    if sector is None:
        return None
    return sector in CYCLICAL_SECTORS


def _is_rate_sensitive(info: dict) -> bool | None:
    """
    Check if security is rate-sensitive.

    Rate-sensitive sectors: REITs, Utilities, Financials, long-duration bonds
    """
    sector = info.get("sector")
    quote_type = info.get("quoteType")
    category = info.get("category")

    # REITs are highly rate-sensitive
    if sector == "Real Estate":
        return True

    # Utilities are rate-sensitive (compete with bonds for yield)
    if sector == "Utilities":
        return True

    # Banks benefit from higher rates (net interest margin)
    if sector in ("Financials", "Financial Services"):
        industry = info.get("industry", "")
        if "Bank" in industry or "Insurance" in industry:
            return True

    # Bond ETFs
    if quote_type == "ETF" and category:
        category_lower = category.lower()
        if any(
            term in category_lower for term in ["bond", "treasury", "fixed income"]
        ):
            return True

    return False


def _is_inflation_hedge(info: dict) -> bool | None:
    """
    Check if security is traditionally an inflation hedge.

    Inflation hedges: commodities, TIPS, real assets, energy, materials
    """
    sector = info.get("sector")
    quote_type = info.get("quoteType")
    category = info.get("category")
    long_name = info.get("longName", "").lower()

    # Energy and materials benefit from inflation
    if sector in ("Energy", "Materials"):
        return True

    # Real estate can be an inflation hedge
    if sector == "Real Estate":
        return True

    # Commodity ETFs
    if quote_type == "ETF":
        if category and "commodit" in category.lower():
            return True
        if any(
            term in long_name for term in ["gold", "silver", "oil", "commodity", "tips"]
        ):
            return True

    return False


def load_to_duckdb(df: pd.DataFrame, table_name: str = "raw_security_characteristics"):
    """
    Load security characteristics into DuckDB database.

    Args:
        df: DataFrame to load
        table_name: Name of the table to create/replace
    """
    print(f"\nLoading security characteristics to DuckDB...")

    db_path = get_db_path()
    print(f"Database: {db_path}")

    con = duckdb.connect(db_path)

    # Drop table if exists and create new one
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

    # Verify the data
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"Loaded {count:,} records to table '{table_name}'")

    # Show sample
    print("\nSample data (key metrics):")
    sample = con.execute(
        f"""
        SELECT
            ticker,
            quote_type,
            sector,
            market_cap_category,
            ROUND(beta, 2) as beta,
            ROUND(trailing_pe, 1) as pe,
            ROUND(dividend_yield * 100, 2) as div_yield_pct,
            is_defensive,
            is_rate_sensitive,
            is_inflation_hedge
        FROM {table_name}
        WHERE beta IS NOT NULL
        ORDER BY market_cap DESC NULLS LAST
        LIMIT 15
    """
    ).df()
    print(sample.to_string(index=False))

    # Show sector distribution
    print("\nSector Distribution:")
    sector_stats = con.execute(
        f"""
        SELECT
            COALESCE(sector, 'Unknown/ETF') as sector,
            COUNT(*) as count,
            ROUND(AVG(beta), 2) as avg_beta,
            ROUND(AVG(trailing_pe), 1) as avg_pe,
            ROUND(AVG(dividend_yield) * 100, 2) as avg_div_yield_pct
        FROM {table_name}
        GROUP BY sector
        ORDER BY count DESC
    """
    ).df()
    print(sector_stats.to_string(index=False))

    # Show scenario-relevant flags
    print("\nScenario-Relevant Classifications:")
    flags_stats = con.execute(
        f"""
        SELECT
            SUM(CASE WHEN is_defensive THEN 1 ELSE 0 END) as defensive,
            SUM(CASE WHEN is_cyclical THEN 1 ELSE 0 END) as cyclical,
            SUM(CASE WHEN is_dividend_payer THEN 1 ELSE 0 END) as dividend_payers,
            SUM(CASE WHEN is_high_growth THEN 1 ELSE 0 END) as high_growth,
            SUM(CASE WHEN is_value THEN 1 ELSE 0 END) as value,
            SUM(CASE WHEN is_rate_sensitive THEN 1 ELSE 0 END) as rate_sensitive,
            SUM(CASE WHEN is_inflation_hedge THEN 1 ELSE 0 END) as inflation_hedge
        FROM {table_name}
    """
    ).df()
    print(flags_stats.to_string(index=False))

    con.close()


def main() -> None:
    """Main execution function."""
    try:
        print("=" * 70)
        print("SECURITY CHARACTERISTICS INGESTION")
        print("=" * 70)
        print("\nThis script fetches fundamental characteristics for scenario analysis.")
        print("Run this weekly as metrics change with prices and quarterly reports.\n")

        # Fetch characteristics
        char_df = fetch_security_characteristics(TICKERS)

        # Load to database
        load_to_duckdb(char_df, "raw_security_characteristics")

        print("\n" + "=" * 70)
        print("SUCCESS: Security characteristics ingestion complete!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Run: cd dbt && dbt run --select stg_security_characteristics")
        print("2. View: Query raw_security_characteristics table in DuckDB")
        print("\nThis data enables LLM-based scenario analysis by providing:")
        print("- Beta and volatility for market sensitivity")
        print("- Valuation metrics (P/E, P/B) for style classification")
        print("- Dividend yield for income-focused scenarios")
        print("- Sector flags for defensive/cyclical/rate-sensitive classification")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
