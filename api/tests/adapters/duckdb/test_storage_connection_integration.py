"""Integration tests for storage connection with LocalStack.

These tests require LocalStack to be running:
    docker compose up localstack

Run with:
    pytest -m integration tests/adapters/duckdb/test_storage_connection_integration.py

Requirements:
    pip install pyarrow s3fs
"""

import os

import pytest

# Skip all tests in this module if LocalStack is not available
pytestmark = pytest.mark.integration

# Check for required dependencies
try:
    import pyarrow
    import s3fs
    INTEGRATION_DEPS_AVAILABLE = True
except ImportError:
    INTEGRATION_DEPS_AVAILABLE = False
    pyarrow = None
    s3fs = None

# Skip entire module if dependencies not available
if not INTEGRATION_DEPS_AVAILABLE:
    pytest.skip("Integration test dependencies not available (pyarrow, s3fs)", allow_module_level=True)


def localstack_available():
    """Check if LocalStack is available."""
    if not INTEGRATION_DEPS_AVAILABLE:
        return False

    import socket

    try:
        host = os.environ.get("LOCALSTACK_HOST", "localhost")
        port = int(os.environ.get("LOCALSTACK_PORT", "4566"))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture
def localstack_config():
    """Create storage config for LocalStack."""
    from adapters.duckdb.storage_connection import (
        StaticCredentialProvider,
        StorageConnectionConfig,
    )

    host = os.environ.get("LOCALSTACK_HOST", "localhost")
    port = os.environ.get("LOCALSTACK_PORT", "4566")

    config = StorageConnectionConfig(
        bucket="test-bucket",
        prefix="test-prefix",
        region="us-east-1",
        credential_type="static",
        access_key_id="test",
        secret_access_key="test",
        endpoint=f"http://{host}:{port}",
    )
    provider = StaticCredentialProvider(
        access_key_id="test",
        secret_access_key="test",
    )
    return config, provider


@pytest.fixture
def setup_localstack_bucket(localstack_config):
    """Create test bucket and upload test parquet file."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    import s3fs

    config, _ = localstack_config
    host = os.environ.get("LOCALSTACK_HOST", "localhost")
    port = os.environ.get("LOCALSTACK_PORT", "4566")

    fs = s3fs.S3FileSystem(
        key="test",
        secret="test",
        endpoint_url=f"http://{host}:{port}",
    )

    # Create bucket if not exists
    try:
        fs.mkdir(config.bucket)
    except Exception:
        pass  # Bucket may already exist

    # Create test parquet file
    table = pa.table({
        "ticker": ["AAPL", "GOOGL", "MSFT"],
        "name": ["Apple", "Google", "Microsoft"],
    })

    path = f"{config.bucket}/{config.prefix}/marts/test_table.parquet"
    with fs.open(path, "wb") as f:
        pq.write_table(table, f)

    yield

    # Cleanup
    try:
        fs.rm(path)
    except Exception:
        pass


@pytest.mark.skipif(
    not localstack_available(),
    reason="LocalStack not available or missing dependencies (pyarrow, s3fs)"
)
class TestLocalStackIntegration:
    """Integration tests with LocalStack."""

    def test_read_parquet_from_localstack(self, localstack_config, setup_localstack_bucket):
        """Can read parquet files from LocalStack S3."""
        from adapters.duckdb.storage_connection import (
            create_storage_connection,
            read_parquet_sql,
        )

        config, provider = localstack_config

        conn = create_storage_connection(config, provider)

        path = config.get_parquet_path("marts", "test_table")
        query = f"SELECT * FROM {read_parquet_sql(path)}"

        result = conn.execute(query).fetchall()
        conn.close()

        assert len(result) == 3
        tickers = [row[0] for row in result]
        assert "AAPL" in tickers
        assert "GOOGL" in tickers
        assert "MSFT" in tickers

    def test_base_repository_with_localstack(self, localstack_config, setup_localstack_bucket):
        """BaseDuckDBRepository works with LocalStack storage config."""
        from adapters.duckdb.base_repository import BaseDuckDBRepository

        config, provider = localstack_config

        repo = BaseDuckDBRepository(
            storage_config=config,
            credential_provider=provider,
        )

        # Get table reference
        table_ref = repo._table_ref("test_table")
        assert "read_parquet" in table_ref
        assert "test_table.parquet" in table_ref

        # Actually read data through the repository's connection
        with repo._get_connection() as conn:
            result = conn.execute(f"SELECT COUNT(*) FROM {table_ref}").fetchone()
            assert result[0] == 3
