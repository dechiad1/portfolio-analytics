"""
Export dbt mart tables to Iceberg format on S3-compatible storage.

This script reads the transformed mart tables from DuckDB (after dbt run)
and exports them to Iceberg tables on S3. The API can then read these
Iceberg tables using DuckDB's Iceberg extension.

Prerequisites:
- dbt run has been completed (mart tables exist in DuckDB)
- S3 credentials configured (S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY)
- Iceberg catalog URI configured (ICEBERG_CATALOG_URI pointing to Postgres)

Usage:
    poetry run python portfolio_analytics/scripts/export_marts_to_iceberg.py

Environment variables:
    S3_ACCESS_KEY_ID: S3 access key
    S3_SECRET_ACCESS_KEY: S3 secret key
    S3_ENDPOINT: S3 endpoint (optional, for non-AWS S3)
    S3_BUCKET: Target S3 bucket
    S3_PREFIX: Path prefix in bucket (default: portfolio-analytics)
    ICEBERG_CATALOG_URI: Postgres URI for Iceberg catalog
"""

import os
import sys
from pathlib import Path

import duckdb
import pyarrow as pa

sys.path.append(str(Path(__file__).parent))
from config import get_db_path
from s3_config import get_s3_config


# Mart tables to export to Iceberg
MART_TABLES = [
    # Dimension tables
    "dim_funds",
    "dim_security",
    "dim_ticker_tracker",
    "dim_asset_classes",
    # Fact tables
    "fct_performance",
    "fact_price_daily",
    "fact_position_daily",
    "fact_portfolio_value_daily",
    # Analytics tables
    "security_historical_mu",
    "security_forward_mu",
    "security_volatility",
]

# Intermediate tables needed for simulation
INTERMEDIATE_TABLES = [
    "int_daily_returns",
]


def get_iceberg_catalog():
    """Create PyIceberg catalog connected to Postgres."""
    from pyiceberg.catalog.sql import SqlCatalog

    catalog_uri = os.getenv("ICEBERG_CATALOG_URI")
    if not catalog_uri:
        raise ValueError(
            "ICEBERG_CATALOG_URI not set. Set it to a Postgres connection string, e.g.:\n"
            "  postgresql://user:pass@host:5432/iceberg_catalog"
        )

    s3_config = get_s3_config()
    if not s3_config:
        raise ValueError(
            "S3 not configured. Set S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, and S3_BUCKET."
        )

    # Build warehouse path
    warehouse_path = f"s3://{s3_config.bucket}/{s3_config.prefix}/iceberg"

    # Catalog configuration
    catalog_config = {
        "uri": catalog_uri,
        "warehouse": warehouse_path,
        "s3.access-key-id": s3_config.access_key_id,
        "s3.secret-access-key": s3_config.secret_access_key,
        "s3.region": s3_config.region,
    }

    if s3_config.endpoint:
        catalog_config["s3.endpoint"] = s3_config.endpoint

    return SqlCatalog("portfolio", **catalog_config)


def read_table_from_duckdb(table_name: str, schema: str = "main_marts") -> pa.Table:
    """Read a table from DuckDB and return as PyArrow table."""
    db_path = get_db_path()
    con = duckdb.connect(db_path, read_only=True)

    try:
        # Read table into PyArrow
        query = f"SELECT * FROM {schema}.{table_name}"
        result = con.execute(query).fetch_arrow_table()
        return result
    finally:
        con.close()


def export_table_to_iceberg(catalog, table_name: str, arrow_table: pa.Table, namespace: str = "marts"):
    """Export a PyArrow table to Iceberg."""
    from pyiceberg.schema import Schema
    from pyiceberg.types import (
        BooleanType,
        DateType,
        DoubleType,
        FloatType,
        IntegerType,
        LongType,
        StringType,
        TimestampType,
        TimestamptzType,
    )
    from pyiceberg.partitioning import PartitionSpec

    # Ensure namespace exists
    try:
        catalog.create_namespace(namespace)
    except Exception:
        pass  # Namespace may already exist

    table_identifier = f"{namespace}.{table_name}"

    # Convert PyArrow schema to Iceberg schema
    def arrow_to_iceberg_type(arrow_type):
        """Convert PyArrow type to Iceberg type."""
        type_str = str(arrow_type)
        if type_str.startswith("int32"):
            return IntegerType()
        elif type_str.startswith("int64"):
            return LongType()
        elif type_str.startswith("float"):
            return FloatType()
        elif type_str.startswith("double"):
            return DoubleType()
        elif type_str.startswith("bool"):
            return BooleanType()
        elif type_str.startswith("date"):
            return DateType()
        elif type_str.startswith("timestamp[us, tz="):
            return TimestamptzType()
        elif type_str.startswith("timestamp"):
            return TimestampType()
        elif type_str.startswith("string") or type_str.startswith("large_string"):
            return StringType()
        elif type_str.startswith("decimal"):
            # For decimals, use double for simplicity
            return DoubleType()
        else:
            # Default to string for unknown types
            return StringType()

    # Build Iceberg schema from Arrow schema
    from pyiceberg.schema import NestedField

    iceberg_fields = []
    for i, field in enumerate(arrow_table.schema):
        iceberg_type = arrow_to_iceberg_type(field.type)
        iceberg_fields.append(
            NestedField(
                field_id=i + 1,
                name=field.name,
                field_type=iceberg_type,
                required=not field.nullable,
            )
        )

    iceberg_schema = Schema(*iceberg_fields)

    # Check if table exists
    try:
        existing_table = catalog.load_table(table_identifier)
        # Table exists - overwrite data
        print(f"  Table {table_identifier} exists, overwriting...")
        existing_table.overwrite(arrow_table)
    except Exception:
        # Table doesn't exist - create it
        print(f"  Creating new table {table_identifier}...")
        table = catalog.create_table(
            identifier=table_identifier,
            schema=iceberg_schema,
            partition_spec=PartitionSpec(),
        )
        table.append(arrow_table)


def main():
    """Export all mart tables to Iceberg."""
    print("=" * 60)
    print("EXPORT MARTS TO ICEBERG")
    print("=" * 60)

    # Verify configuration
    s3_config = get_s3_config()
    if not s3_config:
        print("\nERROR: S3 not configured.")
        print("Set S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, and S3_BUCKET.")
        sys.exit(1)

    catalog_uri = os.getenv("ICEBERG_CATALOG_URI")
    if not catalog_uri:
        print("\nERROR: ICEBERG_CATALOG_URI not set.")
        print("Set it to a Postgres connection string for the Iceberg catalog.")
        sys.exit(1)

    print(f"\nS3 Bucket: {s3_config.bucket}")
    print(f"S3 Prefix: {s3_config.prefix}")
    print(f"S3 Endpoint: {s3_config.endpoint or 'AWS S3 (default)'}")
    print(f"Iceberg Catalog: {catalog_uri.split('@')[0]}@***")  # Hide password

    # Get catalog
    print("\nConnecting to Iceberg catalog...")
    catalog = get_iceberg_catalog()

    # Export mart tables
    print("\nExporting mart tables...")
    print("-" * 60)

    exported = 0
    failed = 0

    for table_name in MART_TABLES:
        try:
            print(f"\nExporting {table_name}...")
            arrow_table = read_table_from_duckdb(table_name, "main_marts")
            print(f"  Read {arrow_table.num_rows} rows from DuckDB")

            export_table_to_iceberg(catalog, table_name, arrow_table, "marts")
            print(f"  Exported to Iceberg")
            exported += 1

        except duckdb.CatalogException as e:
            print(f"  SKIPPED: Table not found in DuckDB ({e})")
            failed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    # Export intermediate tables (for simulation)
    print("\nExporting intermediate tables...")
    print("-" * 60)

    for table_name in INTERMEDIATE_TABLES:
        try:
            print(f"\nExporting {table_name}...")
            arrow_table = read_table_from_duckdb(table_name, "main_intermediate")
            print(f"  Read {arrow_table.num_rows} rows from DuckDB")

            export_table_to_iceberg(catalog, table_name, arrow_table, "intermediate")
            print(f"  Exported to Iceberg")
            exported += 1

        except duckdb.CatalogException as e:
            print(f"  SKIPPED: Table not found in DuckDB ({e})")
            failed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Export complete! Exported: {exported}, Failed/Skipped: {failed}")
    print("=" * 60)

    if failed > 0:
        print("\nNote: Some tables were skipped. Run 'task dbt' first to create them.")


if __name__ == "__main__":
    main()
