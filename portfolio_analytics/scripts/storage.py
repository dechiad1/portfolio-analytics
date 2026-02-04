"""
Storage abstraction layer for OLAP data.

Provides a unified interface for writing raw data to either:
- Local DuckDB file (development)
- S3-compatible storage as Parquet (cloud)

Usage:
    from storage import get_storage

    storage = get_storage()
    storage.write_table(df, "raw_prices")
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import pandas as pd


class Storage(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def write_table(self, df: pd.DataFrame, table_name: str) -> None:
        """Write a DataFrame as a table."""
        pass

    @abstractmethod
    def read_table(self, table_name: str) -> pd.DataFrame:
        """Read a table into a DataFrame."""
        pass

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        pass


class LocalDuckDBStorage(Storage):
    """Local DuckDB file storage for development."""

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def write_table(self, df: pd.DataFrame, table_name: str) -> None:
        """Write DataFrame to DuckDB table."""
        import duckdb

        con = duckdb.connect(str(self._db_path))
        try:
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"Loaded {count:,} records to table '{table_name}'")
        finally:
            con.close()

    def read_table(self, table_name: str) -> pd.DataFrame:
        """Read DuckDB table into DataFrame."""
        import duckdb

        con = duckdb.connect(str(self._db_path), read_only=True)
        try:
            return con.execute(f"SELECT * FROM {table_name}").df()
        finally:
            con.close()

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in DuckDB."""
        import duckdb

        if not self._db_path.exists():
            return False

        con = duckdb.connect(str(self._db_path), read_only=True)
        try:
            result = con.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table_name],
            ).fetchone()
            return result[0] > 0
        except duckdb.CatalogException:
            return False
        finally:
            con.close()


class S3ParquetStorage(Storage):
    """S3-compatible Parquet storage for cloud deployment."""

    def __init__(self, s3_config: "S3Config") -> None:  # noqa: F821
        self._config = s3_config
        self._fs: Optional["s3fs.S3FileSystem"] = None  # noqa: F821

    def _get_fs(self) -> "s3fs.S3FileSystem":  # noqa: F821
        """Get or create S3 filesystem."""
        if self._fs is None:
            import s3fs

            self._fs = s3fs.S3FileSystem(**self._config.get_fsspec_config())
        return self._fs

    def _get_path(self, table_name: str) -> str:
        """Get S3 path for a table."""
        return f"{self._config.bucket}/{self._config.prefix}/raw/{table_name}.parquet"

    def write_table(self, df: pd.DataFrame, table_name: str) -> None:
        """Write DataFrame to S3 as Parquet."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        path = self._get_path(table_name)
        fs = self._get_fs()

        # Convert to PyArrow table and write
        table = pa.Table.from_pandas(df)
        with fs.open(path, "wb") as f:
            pq.write_table(table, f)

        print(f"Wrote {len(df):,} records to s3://{path}")

    def read_table(self, table_name: str) -> pd.DataFrame:
        """Read Parquet from S3 into DataFrame."""
        import pyarrow.parquet as pq

        path = self._get_path(table_name)
        fs = self._get_fs()

        with fs.open(path, "rb") as f:
            table = pq.read_table(f)

        return table.to_pandas()

    def table_exists(self, table_name: str) -> bool:
        """Check if Parquet file exists on S3."""
        path = self._get_path(table_name)
        fs = self._get_fs()
        return fs.exists(path)


def get_storage(force_local: bool = False) -> Storage:
    """
    Get the appropriate storage backend based on configuration.

    Args:
        force_local: If True, always use local DuckDB storage.

    Returns:
        Storage instance (LocalDuckDBStorage or S3ParquetStorage).

    The storage backend is selected based on:
    1. If force_local is True, use local DuckDB
    2. If USE_S3_STORAGE env var is set to "true", use S3
    3. Otherwise, use local DuckDB (default for development)

    Note: S3 is only used when explicitly enabled via USE_S3_STORAGE=true.
    This ensures local development uses DuckDB even if S3 credentials
    happen to be in the environment.
    """
    # Use try/except for imports to handle both module and script contexts
    try:
        from .config import get_db_path
        from .s3_config import get_s3_config
    except ImportError:
        from config import get_db_path
        from s3_config import get_s3_config

    # Check for explicit local mode
    if force_local:
        return LocalDuckDBStorage(get_db_path())

    # Check for explicit S3 mode
    use_s3 = os.getenv("USE_S3_STORAGE", "").lower() == "true"

    if use_s3:
        s3_config = get_s3_config()
        if s3_config is None:
            raise ValueError(
                "USE_S3_STORAGE is set but S3 credentials are not configured. "
                "Set S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, and S3_BUCKET."
            )
        return S3ParquetStorage(s3_config)

    # Default to local storage
    return LocalDuckDBStorage(get_db_path())
