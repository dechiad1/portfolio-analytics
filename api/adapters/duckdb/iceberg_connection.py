"""
DuckDB connection factory for Iceberg tables on S3.

Provides a DuckDB connection configured to read Iceberg tables
from S3-compatible storage using the Iceberg and httpfs extensions.
"""

from dataclasses import dataclass
from typing import Optional

import duckdb


@dataclass(frozen=True)
class IcebergConnectionConfig:
    """Configuration for Iceberg connections via DuckDB."""

    s3_endpoint: Optional[str]
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_region: str
    catalog_uri: str
    catalog_name: str
    namespace: str

    def get_warehouse_path(self, bucket: str, prefix: str) -> str:
        """Get the S3 warehouse path for Iceberg tables."""
        return f"s3://{bucket}/{prefix}/iceberg"


def create_iceberg_connection(config: IcebergConnectionConfig) -> duckdb.DuckDBPyConnection:
    """
    Create a DuckDB connection configured for reading Iceberg tables.

    Args:
        config: Iceberg connection configuration

    Returns:
        Configured DuckDB connection (in-memory)
    """
    # Create in-memory connection
    conn = duckdb.connect(":memory:")

    # Install and load required extensions
    conn.execute("INSTALL httpfs")
    conn.execute("LOAD httpfs")
    conn.execute("INSTALL iceberg")
    conn.execute("LOAD iceberg")

    # Configure S3 credentials
    conn.execute(f"SET s3_access_key_id = '{config.s3_access_key_id}'")
    conn.execute(f"SET s3_secret_access_key = '{config.s3_secret_access_key}'")
    conn.execute(f"SET s3_region = '{config.s3_region}'")

    if config.s3_endpoint:
        conn.execute(f"SET s3_endpoint = '{config.s3_endpoint}'")
        conn.execute("SET s3_url_style = 'path'")
        # Determine SSL based on endpoint
        use_ssl = config.s3_endpoint.startswith("https")
        conn.execute(f"SET s3_use_ssl = {str(use_ssl).lower()}")

    return conn


def get_iceberg_table_path(
    bucket: str,
    prefix: str,
    namespace: str,
    table_name: str
) -> str:
    """
    Get the S3 path to an Iceberg table's metadata.

    Args:
        bucket: S3 bucket name
        prefix: Path prefix in bucket
        namespace: Iceberg namespace (e.g., "marts")
        table_name: Table name

    Returns:
        S3 path to the Iceberg table metadata
    """
    return f"s3://{bucket}/{prefix}/iceberg/{namespace}/{table_name}"


def iceberg_scan_sql(table_path: str) -> str:
    """
    Generate SQL for reading an Iceberg table.

    Args:
        table_path: S3 path to Iceberg table

    Returns:
        SQL expression for scanning the Iceberg table
    """
    return f"iceberg_scan('{table_path}')"
