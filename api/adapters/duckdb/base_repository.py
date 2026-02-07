"""Base class for DuckDB repositories with cloud storage support."""

from pathlib import Path
from typing import Optional

import duckdb

from .storage_connection import (
    CredentialProvider,
    StorageConnectionConfig,
    create_storage_connection,
    read_parquet_sql,
)

# Keep legacy imports for backward compatibility during migration
from .iceberg_connection import IcebergConnectionConfig, create_iceberg_connection


class BaseDuckDBRepository:
    """Base class for DuckDB repositories supporting local and cloud storage modes.

    This class provides common connection management and table reference logic
    for repositories that read from either:
    - A local DuckDB file (development)
    - Parquet files on S3/GCS via DuckDB's httpfs extension (production)

    The key insight is that `read_parquet('s3://path')` returns a table expression
    that can be used directly in FROM clauses and JOINs, just like a regular table.
    This allows us to use identical SQL queries for both modes.
    """

    def __init__(
        self,
        database_path: Optional[str] = None,
        storage_config: Optional[StorageConnectionConfig] = None,
        credential_provider: Optional[CredentialProvider] = None,
        # Legacy parameter for backward compatibility
        iceberg_config: Optional[IcebergConnectionConfig] = None,
    ) -> None:
        """
        Initialize the repository.

        Args:
            database_path: Path to local DuckDB file (for local mode)
            storage_config: Configuration for cloud storage mode
            credential_provider: Provider for storage credentials
            iceberg_config: DEPRECATED - Legacy Iceberg configuration

        Raises:
            ValueError: If no valid configuration is provided
            FileNotFoundError: If database_path is provided but the file doesn't exist
        """
        self._database_path: Optional[Path] = None
        self._storage_config = storage_config
        self._credential_provider = credential_provider
        # Legacy
        self._iceberg_config = iceberg_config

        if storage_config is not None:
            self._mode = "storage"
        elif iceberg_config is not None:
            # Legacy mode
            self._mode = "iceberg"
        elif database_path is not None:
            self._mode = "local"
            self._database_path = Path(database_path)
            if not self._database_path.exists():
                raise FileNotFoundError(
                    f"DuckDB database not found at {self._database_path}"
                )
        else:
            raise ValueError(
                "Either database_path or storage_config must be provided"
            )

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a connection to DuckDB.

        For local mode: connects to the file in read-only mode.
        For storage mode: creates an in-memory connection with httpfs configured.
        For iceberg mode: legacy - creates connection with iceberg extension.
        """
        if self._mode == "storage":
            return create_storage_connection(
                self._storage_config, self._credential_provider
            )
        elif self._mode == "iceberg":
            return create_iceberg_connection(self._iceberg_config)
        else:
            return duckdb.connect(str(self._database_path), read_only=True)

    def _table_ref(self, table_name: str, schema: str = "marts") -> str:
        """
        Get the table reference for a given table name.

        This method returns a string that can be used directly in SQL FROM clauses,
        including JOINs. For storage mode, this returns a read_parquet() function
        call which DuckDB treats as a table expression.

        Args:
            table_name: Name of the table
            schema: Schema/namespace (marts, intermediate)

        Returns:
            Table reference string for SQL queries.
            - Local mode: "main_marts.table_name"
            - Storage mode: "read_parquet('s3://bucket/prefix/namespace/table.parquet')"
            - Iceberg mode: "iceberg_scan('s3://bucket/prefix/iceberg/namespace/table')"
        """
        if self._mode == "storage":
            namespace = "marts" if schema == "marts" else schema.replace("main_", "")
            parquet_path = self._storage_config.get_parquet_path(namespace, table_name)
            return read_parquet_sql(parquet_path)
        elif self._mode == "iceberg":
            from .iceberg_connection import iceberg_scan_sql

            namespace = "marts" if schema == "marts" else schema.replace("main_", "")
            table_path = self._iceberg_config.get_table_path(namespace, table_name)
            return iceberg_scan_sql(table_path)
        else:
            duckdb_schema = f"main_{schema}" if not schema.startswith("main_") else schema
            return f"{duckdb_schema}.{table_name}"
