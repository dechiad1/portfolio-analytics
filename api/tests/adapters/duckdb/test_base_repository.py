"""Tests for BaseDuckDBRepository with storage connection support."""

from unittest.mock import MagicMock, patch
import pytest

from adapters.duckdb.base_repository import BaseDuckDBRepository
from adapters.duckdb.storage_connection import (
    StaticCredentialProvider,
    StorageConnectionConfig,
)


class TestBaseDuckDBRepository:
    """Tests for BaseDuckDBRepository."""

    def test_raises_when_no_config_provided(self):
        """Raises ValueError when neither database_path nor storage_config provided."""
        with pytest.raises(ValueError, match="Either database_path or storage_config"):
            BaseDuckDBRepository()

    def test_raises_when_database_not_found(self, tmp_path):
        """Raises FileNotFoundError when database path doesn't exist."""
        with pytest.raises(FileNotFoundError):
            BaseDuckDBRepository(database_path=str(tmp_path / "nonexistent.db"))

    def test_local_mode_table_ref(self, tmp_path):
        """Table reference in local mode uses DuckDB schema notation."""
        # Create a temporary database file
        import duckdb
        db_path = tmp_path / "test.db"
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE SCHEMA main_marts")
        conn.execute("CREATE TABLE main_marts.dim_funds (ticker VARCHAR)")
        conn.close()

        repo = BaseDuckDBRepository(database_path=str(db_path))
        table_ref = repo._table_ref("dim_funds")

        assert table_ref == "main_marts.dim_funds"

    def test_local_mode_table_ref_intermediate_schema(self, tmp_path):
        """Table reference for intermediate schema works correctly."""
        import duckdb
        db_path = tmp_path / "test.db"
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE SCHEMA main_intermediate")
        conn.execute("CREATE TABLE main_intermediate.int_returns (ticker VARCHAR)")
        conn.close()

        repo = BaseDuckDBRepository(database_path=str(db_path))
        table_ref = repo._table_ref("int_returns", schema="intermediate")

        assert table_ref == "main_intermediate.int_returns"

    def test_storage_mode_table_ref(self):
        """Table reference in storage mode uses read_parquet()."""
        config = StorageConnectionConfig(
            bucket="my-bucket",
            prefix="portfolio-analytics",
            region="us-east-1",
            credential_type="static",
            access_key_id="key",
            secret_access_key="secret",
        )
        provider = StaticCredentialProvider(
            access_key_id="key",
            secret_access_key="secret",
        )

        repo = BaseDuckDBRepository(storage_config=config, credential_provider=provider)
        table_ref = repo._table_ref("dim_funds")

        assert table_ref == "read_parquet('s3://my-bucket/portfolio-analytics/marts/dim_funds.parquet')"

    def test_storage_mode_table_ref_gcs(self):
        """Table reference for GCS uses gs:// prefix."""
        config = StorageConnectionConfig(
            bucket="my-bucket",
            prefix="portfolio-analytics",
            region="us-central1",
            credential_type="adc",
            use_gcs_prefix=True,
        )

        # Mock the ADC provider
        mock_provider = MagicMock()
        mock_provider.get_credentials.return_value = MagicMock(token="test-token")

        repo = BaseDuckDBRepository(storage_config=config, credential_provider=mock_provider)
        table_ref = repo._table_ref("dim_funds")

        assert table_ref == "read_parquet('gs://my-bucket/portfolio-analytics/marts/dim_funds.parquet')"

    def test_storage_mode_table_ref_intermediate(self):
        """Table reference for intermediate schema in storage mode."""
        config = StorageConnectionConfig(
            bucket="my-bucket",
            prefix="portfolio-analytics",
            region="us-east-1",
            credential_type="static",
            access_key_id="key",
            secret_access_key="secret",
        )
        provider = StaticCredentialProvider(
            access_key_id="key",
            secret_access_key="secret",
        )

        repo = BaseDuckDBRepository(storage_config=config, credential_provider=provider)
        table_ref = repo._table_ref("int_returns", schema="intermediate")

        assert table_ref == "read_parquet('s3://my-bucket/portfolio-analytics/intermediate/int_returns.parquet')"
