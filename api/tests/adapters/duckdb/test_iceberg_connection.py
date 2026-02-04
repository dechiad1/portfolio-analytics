"""Tests for Iceberg connection module."""

import pytest

from adapters.duckdb.iceberg_connection import (
    IcebergConnectionConfig,
    _escape_sql_string,
    iceberg_scan_sql,
)


class TestEscapeSqlString:
    """Tests for SQL string escaping."""

    def test_escapes_single_quotes(self):
        """Single quotes are doubled for SQL escaping."""
        assert _escape_sql_string("test'value") == "test''value"

    def test_escapes_multiple_single_quotes(self):
        """Multiple single quotes are all escaped."""
        assert _escape_sql_string("it's a test's value") == "it''s a test''s value"

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert _escape_sql_string("") == ""

    def test_no_quotes(self):
        """String without quotes is unchanged."""
        assert _escape_sql_string("normal_string") == "normal_string"


class TestIcebergConnectionConfig:
    """Tests for IcebergConnectionConfig."""

    def test_get_warehouse_path(self):
        """Warehouse path is correctly constructed."""
        config = IcebergConnectionConfig(
            s3_endpoint=None,
            s3_access_key_id="key",
            s3_secret_access_key="secret",
            s3_region="us-east-1",
            s3_bucket="my-bucket",
            s3_prefix="my-prefix",
            catalog_uri="postgresql://...",
            catalog_name="portfolio",
            namespace="marts",
        )
        assert config.get_warehouse_path() == "s3://my-bucket/my-prefix/iceberg"

    def test_get_table_path(self):
        """Table path is correctly constructed."""
        config = IcebergConnectionConfig(
            s3_endpoint=None,
            s3_access_key_id="key",
            s3_secret_access_key="secret",
            s3_region="us-east-1",
            s3_bucket="my-bucket",
            s3_prefix="my-prefix",
            catalog_uri="postgresql://...",
            catalog_name="portfolio",
            namespace="marts",
        )
        path = config.get_table_path("marts", "dim_funds")
        assert path == "s3://my-bucket/my-prefix/iceberg/marts/dim_funds"

    def test_get_table_path_different_namespace(self):
        """Table path works with different namespace."""
        config = IcebergConnectionConfig(
            s3_endpoint=None,
            s3_access_key_id="key",
            s3_secret_access_key="secret",
            s3_region="us-east-1",
            s3_bucket="bucket",
            s3_prefix="prefix",
            catalog_uri="postgresql://...",
            catalog_name="portfolio",
            namespace="marts",
        )
        path = config.get_table_path("intermediate", "int_daily_returns")
        assert path == "s3://bucket/prefix/iceberg/intermediate/int_daily_returns"

    def test_frozen_config(self):
        """Config is immutable."""
        config = IcebergConnectionConfig(
            s3_endpoint=None,
            s3_access_key_id="key",
            s3_secret_access_key="secret",
            s3_region="us-east-1",
            s3_bucket="bucket",
            s3_prefix="prefix",
            catalog_uri="postgresql://...",
            catalog_name="portfolio",
            namespace="marts",
        )
        with pytest.raises(AttributeError):
            config.s3_bucket = "new-bucket"


class TestIcebergScanSql:
    """Tests for iceberg_scan_sql function."""

    def test_generates_scan_expression(self):
        """iceberg_scan SQL is correctly generated."""
        sql = iceberg_scan_sql("s3://bucket/path/to/table")
        assert sql == "iceberg_scan('s3://bucket/path/to/table')"

    def test_handles_special_characters_in_path(self):
        """Path with special characters is handled."""
        sql = iceberg_scan_sql("s3://my-bucket/my-prefix/iceberg/marts/dim_funds")
        assert sql == "iceberg_scan('s3://my-bucket/my-prefix/iceberg/marts/dim_funds')"
