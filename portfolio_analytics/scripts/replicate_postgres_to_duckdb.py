"""
Replicate Postgres transactional tables to DuckDB/S3 for OLAP analytics.

This script copies data from the Postgres transactional system to storage
(local DuckDB or S3 Parquet) where dbt will transform it into analytical models.

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

import pandas as pd
import psycopg
from psycopg.rows import dict_row

sys.path.append(str(Path(__file__).parent))
from config import get_storage, get_db_path

# Tables to replicate with their column definitions (for schema consistency)
TABLES_TO_REPLICATE = [
    "portfolio",
    "security_registry",
    "security_identifier",
    "equity_details",
    "bond_details",
    "transaction_ledger",
    "position_current",
    "cash_balance",
]

# DuckDB-specific schemas for local mode
DUCKDB_SCHEMAS = {
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
        port=int(os.environ.get("POSTGRES_PORT", "5433")),
        dbname=os.environ.get("POSTGRES_DB", "portfolio_users"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        row_factory=dict_row,
        autocommit=True,
    )


def fetch_table_data(pg_conn, source_table: str) -> pd.DataFrame:
    """Fetch all data from a Postgres table as a DataFrame."""
    with pg_conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {source_table}")
        rows = cur.fetchall()

    if not rows:
        return pd.DataFrame()

    # Convert to DataFrame, handling UUIDs
    df = pd.DataFrame(rows)
    for col in df.columns:
        # Convert UUID columns to strings
        if df[col].apply(lambda x: hasattr(x, 'hex')).any():
            df[col] = df[col].apply(lambda x: str(x) if hasattr(x, 'hex') else x)

    return df


def replicate_to_local_duckdb(pg_conn, db_path: str) -> int:
    """Replicate tables to local DuckDB file."""
    import duckdb

    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    duck_conn = duckdb.connect(db_path)

    total_rows = 0
    for source_table in TABLES_TO_REPLICATE:
        target_table = f"pg_{source_table}"
        print(f"  Replicating {source_table} -> {target_table}...")

        try:
            # Drop and recreate table to handle schema changes
            duck_conn.execute(f"DROP TABLE IF EXISTS {target_table}")
            duck_conn.execute(DUCKDB_SCHEMAS[source_table].replace("IF NOT EXISTS ", ""))

            # Fetch data from Postgres
            df = fetch_table_data(pg_conn, source_table)

            if df.empty:
                print(f"    No data in {source_table}")
                continue

            # Insert using DuckDB's DataFrame registration
            duck_conn.register('df_temp', df)
            duck_conn.execute(f"INSERT INTO {target_table} SELECT * FROM df_temp")
            duck_conn.unregister('df_temp')

            print(f"    Replicated {len(df)} rows")
            total_rows += len(df)

        except psycopg.errors.UndefinedTable:
            print(f"    Table {source_table} does not exist in Postgres (skipping)")
        except Exception as e:
            print(f"    Error replicating {source_table}: {e}")

    duck_conn.close()
    return total_rows


def replicate_to_s3_storage(pg_conn, storage) -> int:
    """Replicate tables to S3 as Parquet files."""
    total_rows = 0
    for source_table in TABLES_TO_REPLICATE:
        target_table = f"pg_{source_table}"
        print(f"  Replicating {source_table} -> {target_table}...")

        try:
            # Fetch data from Postgres
            df = fetch_table_data(pg_conn, source_table)

            if df.empty:
                print(f"    No data in {source_table}")
                continue

            # Write to S3 storage
            storage.write_table(df, target_table)
            total_rows += len(df)

        except psycopg.errors.UndefinedTable:
            print(f"    Table {source_table} does not exist in Postgres (skipping)")
        except Exception as e:
            print(f"    Error replicating {source_table}: {e}")

    return total_rows


def main():
    """Run the replication."""
    print("=" * 60)
    print("Replicating Postgres -> OLAP Storage")
    print("=" * 60)

    pg_conn = None

    try:
        pg_conn = get_postgres_connection()

        # Get storage - this will determine if we use local DuckDB or S3
        storage = get_storage()

        # Check storage type and replicate accordingly
        from storage import LocalDuckDBStorage, S3ParquetStorage

        if isinstance(storage, LocalDuckDBStorage):
            print(f"Target: Local DuckDB ({get_db_path()})")
            total_rows = replicate_to_local_duckdb(pg_conn, get_db_path())
        elif isinstance(storage, S3ParquetStorage):
            print("Target: S3 Parquet storage")
            total_rows = replicate_to_s3_storage(pg_conn, storage)
        else:
            # Fallback to local DuckDB
            print(f"Target: Local DuckDB (fallback)")
            total_rows = replicate_to_local_duckdb(pg_conn, get_db_path())

        print("=" * 60)
        print(f"Replication complete! Total rows: {total_rows}")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        raise

    finally:
        if pg_conn:
            pg_conn.close()


if __name__ == "__main__":
    main()
