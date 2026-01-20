"""
Seed script for common securities.

Pre-populates the security registry with:
- Major ETFs (SPY, QQQ, IWM, VTI, etc.)
- Sample Treasury bonds for learning
- Some blue-chip stocks

Usage:
    cd api
    poetry run python scripts/seed_securities.py
"""

import os
import sys
from datetime import date
from decimal import Decimal
from uuid import uuid4

import psycopg2
from psycopg2.extras import execute_values

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dependencies import load_config


# =============================================================================
# SEED DATA DEFINITIONS
# =============================================================================

ETFS = [
    # (ticker, display_name, sector, exchange)
    ("SPY", "SPDR S&P 500 ETF Trust", "Broad Market", "NYSE"),
    ("QQQ", "Invesco QQQ Trust", "Technology", "NASDAQ"),
    ("IWM", "iShares Russell 2000 ETF", "Small Cap", "NYSE"),
    ("VTI", "Vanguard Total Stock Market ETF", "Broad Market", "NYSE"),
    ("VOO", "Vanguard S&P 500 ETF", "Broad Market", "NYSE"),
    ("VEA", "Vanguard FTSE Developed Markets ETF", "International", "NYSE"),
    ("VWO", "Vanguard FTSE Emerging Markets ETF", "Emerging Markets", "NYSE"),
    ("BND", "Vanguard Total Bond Market ETF", "Fixed Income", "NYSE"),
    ("AGG", "iShares Core US Aggregate Bond ETF", "Fixed Income", "NYSE"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF", "Fixed Income", "NYSE"),
    ("GLD", "SPDR Gold Shares", "Commodities", "NYSE"),
    ("XLF", "Financial Select Sector SPDR Fund", "Financials", "NYSE"),
    ("XLK", "Technology Select Sector SPDR Fund", "Technology", "NYSE"),
    ("XLE", "Energy Select Sector SPDR Fund", "Energy", "NYSE"),
    ("XLV", "Health Care Select Sector SPDR Fund", "Healthcare", "NYSE"),
]

STOCKS = [
    # (ticker, display_name, sector, industry, exchange)
    ("AAPL", "Apple Inc.", "Technology", "Consumer Electronics", "NASDAQ"),
    ("MSFT", "Microsoft Corporation", "Technology", "Software", "NASDAQ"),
    ("GOOGL", "Alphabet Inc.", "Technology", "Internet Services", "NASDAQ"),
    ("AMZN", "Amazon.com Inc.", "Consumer Discretionary", "E-Commerce", "NASDAQ"),
    ("NVDA", "NVIDIA Corporation", "Technology", "Semiconductors", "NASDAQ"),
    ("META", "Meta Platforms Inc.", "Technology", "Social Media", "NASDAQ"),
    ("TSLA", "Tesla Inc.", "Consumer Discretionary", "Automobiles", "NASDAQ"),
    ("JPM", "JPMorgan Chase & Co.", "Financials", "Banking", "NYSE"),
    ("V", "Visa Inc.", "Financials", "Payment Processing", "NYSE"),
    ("JNJ", "Johnson & Johnson", "Healthcare", "Pharmaceuticals", "NYSE"),
    ("WMT", "Walmart Inc.", "Consumer Staples", "Retail", "NYSE"),
    ("PG", "Procter & Gamble Co.", "Consumer Staples", "Household Products", "NYSE"),
    ("XOM", "Exxon Mobil Corporation", "Energy", "Oil & Gas", "NYSE"),
    ("UNH", "UnitedHealth Group Inc.", "Healthcare", "Health Insurance", "NYSE"),
    ("HD", "The Home Depot Inc.", "Consumer Discretionary", "Home Improvement", "NYSE"),
]

# Sample Treasury bonds for learning
# These are representative examples - in production, would be fetched from Treasury API
TREASURY_BONDS = [
    # (display_name, cusip, coupon_type, coupon_rate, frequency, day_count, issue_date, maturity_date, par)
    (
        "US Treasury 2-Year Note 4.25% 2026",
        "91282CKL7",
        "FIXED",
        Decimal("4.25"),
        "SEMIANNUAL",
        "ACT_ACT",
        date(2024, 1, 31),
        date(2026, 1, 31),
        Decimal("100"),
    ),
    (
        "US Treasury 5-Year Note 4.00% 2029",
        "91282CKM5",
        "FIXED",
        Decimal("4.00"),
        "SEMIANNUAL",
        "ACT_ACT",
        date(2024, 1, 31),
        date(2029, 1, 31),
        Decimal("100"),
    ),
    (
        "US Treasury 10-Year Note 4.125% 2034",
        "91282CKN3",
        "FIXED",
        Decimal("4.125"),
        "SEMIANNUAL",
        "ACT_ACT",
        date(2024, 2, 15),
        date(2034, 2, 15),
        Decimal("100"),
    ),
    (
        "US Treasury 30-Year Bond 4.25% 2054",
        "91282CKP8",
        "FIXED",
        Decimal("4.25"),
        "SEMIANNUAL",
        "ACT_ACT",
        date(2024, 2, 15),
        date(2054, 2, 15),
        Decimal("100"),
    ),
    (
        "US Treasury 26-Week Bill 2025",
        "912797KX1",
        "ZERO",
        None,
        "SEMIANNUAL",  # Not applicable but required
        "ACT_360",
        date(2024, 7, 18),
        date(2025, 1, 16),
        Decimal("100"),
    ),
]


def get_connection():
    """Create a database connection from config."""
    config = load_config()
    return psycopg2.connect(
        host=config.database.postgres.host,
        port=config.database.postgres.port,
        database=config.database.postgres.database,
        user=config.database.postgres.user,
        password=config.database.postgres.password,
    )


def seed_etfs(cur):
    """Insert ETF securities."""
    print("Seeding ETFs...")

    for ticker, display_name, sector, exchange in ETFS:
        security_id = uuid4()

        # Insert into security_registry
        cur.execute(
            """
            INSERT INTO security_registry (security_id, asset_type, currency, display_name)
            VALUES (%s, 'ETF', 'USD', %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), display_name),
        )

        # Insert into equity_details
        cur.execute(
            """
            INSERT INTO equity_details (security_id, ticker, exchange, country, sector)
            VALUES (%s, %s, %s, 'USA', %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), ticker, exchange, sector),
        )

        # Insert identifier (TICKER)
        cur.execute(
            """
            INSERT INTO security_identifier (security_id, id_type, id_value, source, is_primary)
            VALUES (%s, 'TICKER', %s, 'seed', true)
            ON CONFLICT (id_type, id_value) DO NOTHING
            """,
            (str(security_id), ticker),
        )

    print(f"  Inserted {len(ETFS)} ETFs")


def seed_stocks(cur):
    """Insert stock securities."""
    print("Seeding stocks...")

    for ticker, display_name, sector, industry, exchange in STOCKS:
        security_id = uuid4()

        # Insert into security_registry
        cur.execute(
            """
            INSERT INTO security_registry (security_id, asset_type, currency, display_name)
            VALUES (%s, 'EQUITY', 'USD', %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), display_name),
        )

        # Insert into equity_details
        cur.execute(
            """
            INSERT INTO equity_details (security_id, ticker, exchange, country, sector, industry)
            VALUES (%s, %s, %s, 'USA', %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), ticker, exchange, sector, industry),
        )

        # Insert identifier (TICKER)
        cur.execute(
            """
            INSERT INTO security_identifier (security_id, id_type, id_value, source, is_primary)
            VALUES (%s, 'TICKER', %s, 'seed', true)
            ON CONFLICT (id_type, id_value) DO NOTHING
            """,
            (str(security_id), ticker),
        )

    print(f"  Inserted {len(STOCKS)} stocks")


def seed_treasury_bonds(cur):
    """Insert Treasury bond securities."""
    print("Seeding Treasury bonds...")

    for (
        display_name,
        cusip,
        coupon_type,
        coupon_rate,
        frequency,
        day_count,
        issue_date,
        maturity_date,
        par_value,
    ) in TREASURY_BONDS:
        security_id = uuid4()

        # Insert into security_registry
        cur.execute(
            """
            INSERT INTO security_registry (security_id, asset_type, currency, display_name)
            VALUES (%s, 'BOND', 'USD', %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), display_name),
        )

        # Insert into bond_details
        cur.execute(
            """
            INSERT INTO bond_details (
                security_id, issuer_name, coupon_type, coupon_rate,
                payment_frequency, day_count_convention,
                issue_date, maturity_date, par_value
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                str(security_id),
                "U.S. Treasury",
                coupon_type,
                coupon_rate,
                frequency,
                day_count,
                issue_date,
                maturity_date,
                par_value,
            ),
        )

        # Insert identifier (CUSIP)
        cur.execute(
            """
            INSERT INTO security_identifier (security_id, id_type, id_value, source, is_primary)
            VALUES (%s, 'CUSIP', %s, 'seed', true)
            ON CONFLICT (id_type, id_value) DO NOTHING
            """,
            (str(security_id), cusip),
        )

    print(f"  Inserted {len(TREASURY_BONDS)} Treasury bonds")


def seed_demo_portfolio(cur):
    """Create a demo portfolio for testing."""
    print("Creating demo portfolio...")

    portfolio_id = uuid4()
    demo_user_id = uuid4()

    cur.execute(
        """
        INSERT INTO portfolio (portfolio_id, user_id, name, base_currency)
        VALUES (%s, %s, %s, 'USD')
        ON CONFLICT DO NOTHING
        RETURNING portfolio_id
        """,
        (str(portfolio_id), str(demo_user_id), "Demo Portfolio"),
    )

    result = cur.fetchone()
    if result:
        print(f"  Created demo portfolio: {portfolio_id}")
        # Initialize cash balance
        cur.execute(
            """
            INSERT INTO cash_balance (portfolio_id, currency, balance)
            VALUES (%s, 'USD', 100000.00)
            ON CONFLICT DO NOTHING
            """,
            (str(portfolio_id),),
        )
        print("  Initialized with $100,000 USD cash balance")
    else:
        print("  Demo portfolio already exists")


def main():
    """Run all seed operations."""
    print("=" * 60)
    print("Seeding security registry...")
    print("=" * 60)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            seed_etfs(cur)
            seed_stocks(cur)
            seed_treasury_bonds(cur)
            seed_demo_portfolio(cur)

        conn.commit()
        print("=" * 60)
        print("Seeding complete!")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
