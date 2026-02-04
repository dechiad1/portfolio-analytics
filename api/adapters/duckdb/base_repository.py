"""Base class for DuckDB repositories with S3/Iceberg support."""

from pathlib import Path
from typing import Optional

import duckdb

from .iceberg_connection import IcebergConnectionConfig, create_iceberg_connection


class BaseDuckDBRepository:
    """Base class for DuckDB repositories supporting both local and S3/Iceberg modes.

    This class provides common connection management and table reference logic
    for repositories that read from either:
    - A local DuckDB file (development)
    - Iceberg tables on S3 via DuckDB's iceberg extension (production)

    The key insight is that `iceberg_scan('s3://path')` returns a table expression
    that can be used directly in FROM clauses and JOINs, just like a regular table.
    This allows us to use identical SQL queries for both modes.
    """

    def __init__(
        self,
        database_path: Optional[str] = None,
        iceberg_config: Optional[IcebergConnectionConfig] = None,
    ) -> None:
        """
        Initialize the repository.

        Args:
            database_path: Path to local DuckDB file (for local mode)
            iceberg_config: Configuration for Iceberg mode (mutually exclusive with database_path)

        Raises:
            ValueError: If neither database_path nor iceberg_config is provided
            FileNotFoundError: If database_path is provided but the file doesn't exist
        """
        self._database_path: Optional[Path] = None
        self._iceberg_config = iceberg_config

        if iceberg_config is not None:
            self._mode = "iceberg"
        elif database_path is not None:
            self._mode = "local"
            self._database_path = Path(database_path)
            if not self._database_path.exists():
                raise FileNotFoundError(
                    f"DuckDB database not found at {self._database_path}"
                )
        else:
            raise ValueError("Either database_path or iceberg_config must be provided")

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a connection to DuckDB.

        For local mode: connects to the file in read-only mode.
        For iceberg mode: creates an in-memory connection with S3/httpfs configured.
        """
        if self._mode == "iceberg":
            return create_iceberg_connection(self._iceberg_config)
        else:
            return duckdb.connect(str(self._database_path), read_only=True)

    def _table_ref(self, table_name: str, schema: str = "marts") -> str:
        """
        Get the table reference for a given table name.

        This method returns a string that can be used directly in SQL FROM clauses,
        including JOINs. For iceberg mode, this returns an iceberg_scan() function
        call which DuckDB treats as a table expression.

        Args:
            table_name: Name of the table
            schema: Schema/namespace (marts, intermediate)

        Returns:
            Table reference string for SQL queries.
            - Local mode: "main_marts.table_name"
            - Iceberg mode: "iceberg_scan('s3://bucket/prefix/iceberg/namespace/table')"
        """
        if self._mode == "iceberg":
            from .iceberg_connection import iceberg_scan_sql

            namespace = "marts" if schema == "marts" else schema.replace("main_", "")
            table_path = self._iceberg_config.get_table_path(namespace, table_name)
            return iceberg_scan_sql(table_path)
        else:
            duckdb_schema = f"main_{schema}" if not schema.startswith("main_") else schema
            return f"{duckdb_schema}.{table_name}"
