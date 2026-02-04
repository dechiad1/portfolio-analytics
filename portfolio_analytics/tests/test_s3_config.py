"""Tests for S3 configuration module."""

import os
from unittest.mock import patch

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from s3_config import S3Config, get_s3_config


class TestS3Config:
    """Tests for S3Config class."""

    def test_from_env_with_all_vars(self):
        """Config is loaded from environment variables."""
        env = {
            "S3_ENDPOINT": "http://localhost:9000",
            "S3_ACCESS_KEY_ID": "test-key",
            "S3_SECRET_ACCESS_KEY": "test-secret",
            "S3_BUCKET": "test-bucket",
            "S3_PREFIX": "test-prefix",
            "S3_REGION": "us-west-2",
        }
        with patch.dict(os.environ, env, clear=True):
            config = S3Config.from_env()
            assert config.endpoint == "http://localhost:9000"
            assert config.access_key_id == "test-key"
            assert config.secret_access_key == "test-secret"
            assert config.bucket == "test-bucket"
            assert config.prefix == "test-prefix"
            assert config.region == "us-west-2"

    def test_from_env_with_defaults(self):
        """Default values are used when env vars not set."""
        env = {
            "S3_ACCESS_KEY_ID": "key",
            "S3_SECRET_ACCESS_KEY": "secret",
            "S3_BUCKET": "bucket",
        }
        with patch.dict(os.environ, env, clear=True):
            config = S3Config.from_env()
            assert config.endpoint is None
            assert config.prefix == "portfolio-analytics"
            assert config.region == "us-east-1"

    def test_from_env_empty_endpoint_becomes_none(self):
        """Empty S3_ENDPOINT becomes None."""
        env = {
            "S3_ENDPOINT": "  ",  # whitespace only
            "S3_ACCESS_KEY_ID": "key",
            "S3_SECRET_ACCESS_KEY": "secret",
            "S3_BUCKET": "bucket",
        }
        with patch.dict(os.environ, env, clear=True):
            config = S3Config.from_env()
            assert config.endpoint is None

    def test_is_configured_with_all_required(self):
        """is_configured returns True when all required fields set."""
        config = S3Config(
            endpoint=None,
            access_key_id="key",
            secret_access_key="secret",
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
        )
        assert config.is_configured() is True

    def test_is_configured_missing_access_key(self):
        """is_configured returns False when access key missing."""
        config = S3Config(
            endpoint=None,
            access_key_id="",
            secret_access_key="secret",
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
        )
        assert config.is_configured() is False

    def test_is_configured_missing_secret(self):
        """is_configured returns False when secret missing."""
        config = S3Config(
            endpoint=None,
            access_key_id="key",
            secret_access_key="",
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
        )
        assert config.is_configured() is False

    def test_is_configured_missing_bucket(self):
        """is_configured returns False when bucket missing."""
        config = S3Config(
            endpoint=None,
            access_key_id="key",
            secret_access_key="secret",
            bucket="",
            prefix="prefix",
            region="us-east-1",
        )
        assert config.is_configured() is False

    def test_get_raw_path(self):
        """Raw path is correctly constructed."""
        config = S3Config(
            endpoint=None,
            access_key_id="key",
            secret_access_key="secret",
            bucket="my-bucket",
            prefix="my-prefix",
            region="us-east-1",
        )
        assert config.get_raw_path("raw_prices") == "s3://my-bucket/my-prefix/raw/raw_prices.parquet"

    def test_get_iceberg_path(self):
        """Iceberg path is correctly constructed."""
        config = S3Config(
            endpoint=None,
            access_key_id="key",
            secret_access_key="secret",
            bucket="my-bucket",
            prefix="my-prefix",
            region="us-east-1",
        )
        assert config.get_iceberg_path("dim_funds") == "s3://my-bucket/my-prefix/iceberg/marts/dim_funds"

    def test_get_duckdb_s3_config_without_endpoint(self):
        """DuckDB config without custom endpoint."""
        config = S3Config(
            endpoint=None,
            access_key_id="key",
            secret_access_key="secret",
            bucket="bucket",
            prefix="prefix",
            region="eu-west-1",
        )
        duckdb_config = config.get_duckdb_s3_config()
        assert duckdb_config == {
            "s3_access_key_id": "key",
            "s3_secret_access_key": "secret",
            "s3_region": "eu-west-1",
        }

    def test_get_duckdb_s3_config_with_https_endpoint(self):
        """DuckDB config with HTTPS endpoint."""
        config = S3Config(
            endpoint="https://storage.googleapis.com",
            access_key_id="key",
            secret_access_key="secret",
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
        )
        duckdb_config = config.get_duckdb_s3_config()
        assert duckdb_config["s3_endpoint"] == "https://storage.googleapis.com"
        assert duckdb_config["s3_url_style"] == "path"
        assert duckdb_config["s3_use_ssl"] == "true"

    def test_get_duckdb_s3_config_with_http_endpoint(self):
        """DuckDB config with HTTP endpoint (MinIO local)."""
        config = S3Config(
            endpoint="http://localhost:9000",
            access_key_id="key",
            secret_access_key="secret",
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
        )
        duckdb_config = config.get_duckdb_s3_config()
        assert duckdb_config["s3_use_ssl"] == "false"

    def test_get_fsspec_config_without_endpoint(self):
        """fsspec config without custom endpoint."""
        config = S3Config(
            endpoint=None,
            access_key_id="key",
            secret_access_key="secret",
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
        )
        fsspec_config = config.get_fsspec_config()
        assert fsspec_config == {"key": "key", "secret": "secret"}

    def test_get_fsspec_config_with_endpoint(self):
        """fsspec config with custom endpoint."""
        config = S3Config(
            endpoint="http://localhost:9000",
            access_key_id="key",
            secret_access_key="secret",
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
        )
        fsspec_config = config.get_fsspec_config()
        assert fsspec_config == {
            "key": "key",
            "secret": "secret",
            "client_kwargs": {"endpoint_url": "http://localhost:9000"},
        }


class TestGetS3Config:
    """Tests for get_s3_config function."""

    def test_returns_config_when_configured(self):
        """Returns S3Config when properly configured."""
        env = {
            "S3_ACCESS_KEY_ID": "key",
            "S3_SECRET_ACCESS_KEY": "secret",
            "S3_BUCKET": "bucket",
        }
        with patch.dict(os.environ, env, clear=True):
            config = get_s3_config()
            assert config is not None
            assert config.bucket == "bucket"

    def test_returns_none_when_not_configured(self):
        """Returns None when S3 not configured."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_s3_config()
            assert config is None
