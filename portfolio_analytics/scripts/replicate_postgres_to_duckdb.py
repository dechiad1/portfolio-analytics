"""
Replicate Postgres transactional tables to DuckDB for OLAP analytics.

This script copies data from the Postgres transactional system to DuckDB
where dbt will transform it into analytical models.

Tables replicated:
- portfolio -> pg_portfolio
- security_registry -> pg_security_registry
- security_identifier -> pg_security_identifier
- equity_details -> pg_equity_details
- bond_details -> pg_bond_details
- transaction_ledger -> pg_transaction_ledger
- position_current -> pg_position_current
- cash_balance -> pg_cash_balance

Usage:
    poetry run python scripts/replicate_postgres_to_duckdb.py
"""

import os
import sys
from pathlib import Path

import duckdb
import psycopg
from psycopg.rows import dict_row

# Configuration
DUCKDB_PATH = Path(__file__).parent.parent / "data" / "portfolio.duckdb"

# Tables to replicate with their schemas
TABLES_TO_REPLICATE = {
    "portfolio": """
        CREATE TABLE IF NOT EXISTS pg_portfolio (
            portfolio_id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            base_currency VARCHAR(3) NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """,
    "security_registry": """
        CREATE TABLE IF NOT EXISTS pg_security_registry (
            security_id VARCHAR PRIMARY KEY,
            asset_type VARCHAR NOT NULL,
            currency VARCHAR(3) NOT NULL,
            display_name VARCHAR NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """,
    "security_identifier": """
        CREATE TABLE IF NOT EXISTS pg_security_identifier (
            id VARCHAR PRIMARY KEY,
            security_id VARCHAR NOT NULL,
            id_type VARCHAR NOT NULL,
            id_value VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            is_primary BOOLEAN NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """,
    "equity_details": """
        CREATE TABLE IF NOT EXISTS pg_equity_details (
            security_id VARCHAR PRIMARY KEY,
            ticker VARCHAR NOT NULL,
            exchange VARCHAR,
            country VARCHAR,
            sector VARCHAR,
            industry VARCHAR,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """,
    "bond_details": """
        CREATE TABLE IF NOT EXISTS pg_bond_details (
            security_id VARCHAR PRIMARY KEY,
            issuer_name VARCHAR NOT NULL,
            coupon_type VARCHAR NOT NULL,
            coupon_rate DECIMAL(10, 6),
            payment_frequency VARCHAR NOT NULL,
            day_count_convention VARCHAR NOT NULL,
            issue_date DATE NOT NULL,
            maturity_date DATE NOT NULL,
            par_value DECIMAL(18, 6) NOT NULL,
            price_quote_convention VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """,
    "transaction_ledger": """
        CREATE TABLE IF NOT EXISTS pg_transaction_ledger (
            txn_id VARCHAR PRIMARY KEY,
            portfolio_id VARCHAR NOT NULL,
            event_ts TIMESTAMP NOT NULL,
            txn_type VARCHAR NOT NULL,
            security_id VARCHAR,
            quantity DECIMAL(18, 8) NOT NULL,
            price DECIMAL(18, 8),
            fees DECIMAL(18, 8) NOT NULL,
            currency VARCHAR(3) NOT NULL,
            notes VARCHAR,
            created_at TIMESTAMP NOT NULL
        )
    """,
    "position_current": """
        CREATE TABLE IF NOT EXISTS pg_position_current (
            portfolio_id VARCHAR NOT NULL,
            security_id VARCHAR NOT NULL,
            quantity DECIMAL(18, 8) NOT NULL,
            avg_cost DECIMAL(18, 8) NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (portfolio_id, security_id)
        )
    """,
    "cash_balance": """
        CREATE TABLE IF NOT EXISTS pg_cash_balance (
            portfolio_id VARCHAR NOT NULL,
            currency VARCHAR(3) NOT NULL,
            balance DECIMAL(18, 8) NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (portfolio_id, currency)
        )
    """,
}


def get_postgres_connection():
    """Create Postgres connection from environment or defaults."""
    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "portfolio_analytics"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        row_factory=dict_row,
        autocommit=True,
    )


def get_duckdb_connection():
    """Create DuckDB connection."""
    # Ensure data directory exists
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DUCKDB_PATH))


def replicate_table(pg_conn, duck_conn, source_table: str, create_sql: str):
    """Replicate a single table from Postgres to DuckDB."""
    target_table = f"pg_{source_table}"
    print(f"  Replicating {source_table} -> {target_table}...")

    # Create table in DuckDB
    duck_conn.execute(create_sql)

    # Truncate existing data
    duck_conn.execute(f"DELETE FROM {target_table}")

    # Fetch all data from Postgres (row_factory=dict_row set on connection)
    with pg_conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {source_table}")
        rows = cur.fetchall()

    if not rows:
        print(f"    No data in {source_table}")
        return 0

    # Get column names from first row
    columns = list(rows[0].keys())

    # Build insert statement
    placeholders = ", ".join(["?" for _ in columns])
    column_list = ", ".join(columns)
    insert_sql = f"INSERT INTO {target_table} ({column_list}) VALUES ({placeholders})"

    # Insert all rows
    for row in rows:
        # Convert UUIDs to strings
        values = [str(v) if hasattr(v, "hex") else v for v in row.values()]
        duck_conn.execute(insert_sql, values)

    print(f"    Replicated {len(rows)} rows")
    return len(rows)


def main():
    """Run the replication."""
    print("=" * 60)
    print("Replicating Postgres -> DuckDB")
    print("=" * 60)

    pg_conn = None
    duck_conn = None

    try:
        pg_conn = get_postgres_connection()
        duck_conn = get_duckdb_connection()

        total_rows = 0
        for source_table, create_sql in TABLES_TO_REPLICATE.items():
            try:
                rows = replicate_table(pg_conn, duck_conn, source_table, create_sql)
                total_rows += rows
            except psycopg.errors.UndefinedTable:
                print(f"    Table {source_table} does not exist in Postgres (skipping)")
            except Exception as e:
                print(f"    Error replicating {source_table}: {e}")

        print("=" * 60)
        print(f"Replication complete! Total rows: {total_rows}")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        raise

    finally:
        if pg_conn:
            pg_conn.close()
        if duck_conn:
            duck_conn.close()


if __name__ == "__main__":
    main()
