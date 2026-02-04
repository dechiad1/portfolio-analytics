"""Tests for storage abstraction module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from storage import LocalDuckDBStorage, get_storage


class TestLocalDuckDBStorage:
    """Tests for LocalDuckDBStorage class."""

    def test_creates_parent_directory(self):
        """Parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "subdir" / "nested" / "test.duckdb"
            storage = LocalDuckDBStorage(str(db_path))
            assert db_path.parent.exists()

    def test_write_and_read_table(self):
        """Can write and read a DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.duckdb"
            storage = LocalDuckDBStorage(str(db_path))

            # Write test data
            df = pd.DataFrame({
                "ticker": ["AAPL", "GOOGL", "MSFT"],
                "price": [150.0, 2800.0, 300.0],
            })
            storage.write_table(df, "test_table")

            # Read it back
            result = storage.read_table("test_table")
            assert len(result) == 3
            assert list(result["ticker"]) == ["AAPL", "GOOGL", "MSFT"]

    def test_write_overwrites_existing_table(self):
        """Writing to existing table replaces the data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.duckdb"
            storage = LocalDuckDBStorage(str(db_path))

            # Write initial data
            df1 = pd.DataFrame({"value": [1, 2, 3]})
            storage.write_table(df1, "test_table")

            # Write new data
            df2 = pd.DataFrame({"value": [4, 5]})
            storage.write_table(df2, "test_table")

            # Verify new data
            result = storage.read_table("test_table")
            assert len(result) == 2
            assert list(result["value"]) == [4, 5]

    def test_table_exists_true(self):
        """table_exists returns True for existing table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.duckdb"
            storage = LocalDuckDBStorage(str(db_path))

            df = pd.DataFrame({"col": [1]})
            storage.write_table(df, "existing_table")

            assert storage.table_exists("existing_table") is True

    def test_table_exists_false_no_table(self):
        """table_exists returns False for non-existent table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.duckdb"
            storage = LocalDuckDBStorage(str(db_path))

            # Create a table so db file exists
            df = pd.DataFrame({"col": [1]})
            storage.write_table(df, "other_table")

            assert storage.table_exists("nonexistent") is False

    def test_table_exists_false_no_database(self):
        """table_exists returns False when database doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nonexistent.duckdb"
            storage = LocalDuckDBStorage(str(db_path))

            assert storage.table_exists("any_table") is False


class TestGetStorage:
    """Tests for get_storage function."""

    def test_force_local_returns_local_storage(self):
        """force_local=True always returns LocalDuckDBStorage."""
        with patch.dict(os.environ, {"USE_S3_STORAGE": "true"}, clear=False):
            storage = get_storage(force_local=True)
            assert isinstance(storage, LocalDuckDBStorage)

    def test_default_returns_local_storage(self):
        """Default (no S3 env vars) returns LocalDuckDBStorage."""
        with patch.dict(os.environ, {}, clear=True):
            # Need to preserve some env vars for config
            storage = get_storage()
            assert isinstance(storage, LocalDuckDBStorage)

    def test_use_s3_without_config_raises(self):
        """USE_S3_STORAGE=true without config raises ValueError."""
        env = {"USE_S3_STORAGE": "true"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="S3 credentials are not configured"):
                get_storage()

    def test_use_s3_with_config_returns_s3_storage(self):
        """USE_S3_STORAGE=true with config returns S3ParquetStorage."""
        env = {
            "USE_S3_STORAGE": "true",
            "S3_ACCESS_KEY_ID": "test-key",
            "S3_SECRET_ACCESS_KEY": "test-secret",
            "S3_BUCKET": "test-bucket",
        }
        with patch.dict(os.environ, env, clear=True):
            from storage import S3ParquetStorage
            storage = get_storage()
            assert isinstance(storage, S3ParquetStorage)

    def test_use_s3_case_insensitive(self):
        """USE_S3_STORAGE check is case-insensitive."""
        env = {
            "USE_S3_STORAGE": "TRUE",
            "S3_ACCESS_KEY_ID": "test-key",
            "S3_SECRET_ACCESS_KEY": "test-secret",
            "S3_BUCKET": "test-bucket",
        }
        with patch.dict(os.environ, env, clear=True):
            from storage import S3ParquetStorage
            storage = get_storage()
            assert isinstance(storage, S3ParquetStorage)
