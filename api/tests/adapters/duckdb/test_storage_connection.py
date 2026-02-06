"""Tests for storage connection module with GCS/ADC support."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# These imports will fail until we implement the module
from adapters.duckdb.storage_connection import (
    ADCCredentialProvider,
    CredentialProvider,
    StaticCredentialProvider,
    StorageConnectionConfig,
    create_storage_connection,
    read_parquet_sql,
)


class TestStorageConnectionConfig:
    """Tests for StorageConnectionConfig."""

    def test_create_with_static_credentials(self):
        """Config can be created with static credentials."""
        config = StorageConnectionConfig(
            bucket="my-bucket",
            prefix="portfolio-analytics",
            region="us-east-1",
            credential_type="static",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )
        assert config.bucket == "my-bucket"
        assert config.credential_type == "static"
        assert config.access_key_id == "AKIAIOSFODNN7EXAMPLE"

    def test_create_with_adc_credentials(self):
        """Config can be created with ADC credential type."""
        config = StorageConnectionConfig(
            bucket="my-gcs-bucket",
            prefix="portfolio-analytics",
            region="us-central1",
            credential_type="adc",
        )
        assert config.bucket == "my-gcs-bucket"
        assert config.credential_type == "adc"
        assert config.access_key_id is None

    def test_create_with_endpoint_for_localstack(self):
        """Config can include custom endpoint for LocalStack."""
        config = StorageConnectionConfig(
            bucket="local-bucket",
            prefix="portfolio-analytics",
            region="us-east-1",
            credential_type="static",
            access_key_id="test",
            secret_access_key="test",
            endpoint="http://localhost:4566",
        )
        assert config.endpoint == "http://localhost:4566"

    def test_get_parquet_path(self):
        """Parquet path is correctly constructed."""
        config = StorageConnectionConfig(
            bucket="my-bucket",
            prefix="portfolio-analytics",
            region="us-east-1",
            credential_type="static",
            access_key_id="key",
            secret_access_key="secret",
        )
        path = config.get_parquet_path("marts", "dim_funds")
        assert path == "s3://my-bucket/portfolio-analytics/marts/dim_funds.parquet"

    def test_get_parquet_path_gcs(self):
        """Parquet path for GCS uses gs:// prefix."""
        config = StorageConnectionConfig(
            bucket="my-gcs-bucket",
            prefix="portfolio-analytics",
            region="us-central1",
            credential_type="adc",
            use_gcs_prefix=True,
        )
        path = config.get_parquet_path("marts", "dim_funds")
        assert path == "gs://my-gcs-bucket/portfolio-analytics/marts/dim_funds.parquet"

    def test_frozen_config(self):
        """Config is immutable."""
        config = StorageConnectionConfig(
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
            credential_type="static",
            access_key_id="key",
            secret_access_key="secret",
        )
        with pytest.raises(AttributeError):
            config.bucket = "new-bucket"


class TestStaticCredentialProvider:
    """Tests for StaticCredentialProvider."""

    def test_provides_static_credentials(self):
        """Returns the configured static credentials."""
        provider = StaticCredentialProvider(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )
        creds = provider.get_credentials()
        assert creds.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert creds.secret_access_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert creds.token is None

    def test_never_needs_refresh(self):
        """Static credentials never need refresh."""
        provider = StaticCredentialProvider(
            access_key_id="key",
            secret_access_key="secret",
        )
        assert provider.needs_refresh() is False


class TestADCCredentialProvider:
    """Tests for ADCCredentialProvider with Google Cloud ADC."""

    def _create_mock_google_auth(self, mock_credentials):
        """Create mock functions for google.auth."""
        mock_auth_default = MagicMock(return_value=(mock_credentials, "test-project"))
        mock_auth_request = MagicMock()
        return mock_auth_default, mock_auth_request

    @patch("adapters.duckdb.storage_connection._get_google_auth")
    def test_gets_credentials_from_adc(self, mock_get_google_auth):
        """Gets credentials using google.auth.default()."""
        mock_credentials = MagicMock()
        mock_credentials.token = "ya29.test-token"
        mock_credentials.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_credentials.expired = False

        mock_auth_default, mock_auth_request = self._create_mock_google_auth(mock_credentials)
        mock_get_google_auth.return_value = (mock_auth_default, mock_auth_request)

        provider = ADCCredentialProvider()
        creds = provider.get_credentials()

        mock_auth_default.assert_called_once()
        assert creds.token == "ya29.test-token"

    @patch("adapters.duckdb.storage_connection._get_google_auth")
    def test_refreshes_expired_token(self, mock_get_google_auth):
        """Refreshes token when expired."""
        mock_credentials = MagicMock()
        mock_credentials.token = "expired-token"
        mock_credentials.expiry = datetime.now(timezone.utc) - timedelta(minutes=10)
        mock_credentials.expired = True

        mock_auth_default, mock_auth_request = self._create_mock_google_auth(mock_credentials)
        mock_get_google_auth.return_value = (mock_auth_default, mock_auth_request)

        provider = ADCCredentialProvider()
        provider.get_credentials()

        mock_credentials.refresh.assert_called_once()

    @patch("adapters.duckdb.storage_connection._get_google_auth")
    def test_needs_refresh_when_expiring_soon(self, mock_get_google_auth):
        """Reports need for refresh when token expires within threshold."""
        mock_credentials = MagicMock()
        mock_credentials.token = "soon-to-expire"
        # Expires in 3 minutes (less than default 5 min threshold)
        mock_credentials.expiry = datetime.now(timezone.utc) + timedelta(minutes=3)
        mock_credentials.expired = False

        mock_auth_default, mock_auth_request = self._create_mock_google_auth(mock_credentials)
        mock_get_google_auth.return_value = (mock_auth_default, mock_auth_request)

        provider = ADCCredentialProvider(refresh_threshold_minutes=5)
        provider.get_credentials()  # Initialize credentials

        assert provider.needs_refresh() is True

    @patch("adapters.duckdb.storage_connection._get_google_auth")
    def test_no_refresh_needed_when_token_valid(self, mock_get_google_auth):
        """Does not need refresh when token has plenty of time remaining."""
        mock_credentials = MagicMock()
        mock_credentials.token = "valid-token"
        mock_credentials.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_credentials.expired = False

        mock_auth_default, mock_auth_request = self._create_mock_google_auth(mock_credentials)
        mock_get_google_auth.return_value = (mock_auth_default, mock_auth_request)

        provider = ADCCredentialProvider(refresh_threshold_minutes=5)
        provider.get_credentials()

        assert provider.needs_refresh() is False

    @patch("adapters.duckdb.storage_connection._get_google_auth")
    def test_lazy_initialization(self, mock_get_google_auth):
        """Credentials are not fetched until first access."""
        mock_credentials = MagicMock()
        mock_credentials.expired = False
        mock_credentials.expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_auth_default, mock_auth_request = self._create_mock_google_auth(mock_credentials)
        mock_get_google_auth.return_value = (mock_auth_default, mock_auth_request)

        provider = ADCCredentialProvider()

        # _get_google_auth not called yet (lazy)
        mock_get_google_auth.assert_not_called()

        # Now fetch credentials - this triggers initialization
        provider.get_credentials()
        mock_get_google_auth.assert_called_once()
        mock_auth_default.assert_called_once()

    @patch("adapters.duckdb.storage_connection._get_google_auth")
    def test_raises_import_error_when_google_auth_unavailable(self, mock_get_google_auth):
        """Raises ImportError when google-auth is not installed."""
        mock_get_google_auth.return_value = (None, None)

        provider = ADCCredentialProvider()

        with pytest.raises(ImportError, match="google-auth package is required"):
            provider.get_credentials()


class TestReadParquetSql:
    """Tests for read_parquet_sql function."""

    def test_generates_read_parquet_expression(self):
        """read_parquet SQL is correctly generated."""
        sql = read_parquet_sql("s3://bucket/path/to/table.parquet")
        assert sql == "read_parquet('s3://bucket/path/to/table.parquet')"

    def test_handles_gcs_prefix(self):
        """GCS paths are handled correctly."""
        sql = read_parquet_sql("gs://bucket/path/to/table.parquet")
        assert sql == "read_parquet('gs://bucket/path/to/table.parquet')"


class TestCreateStorageConnection:
    """Tests for create_storage_connection function."""

    def test_creates_connection_with_static_credentials(self):
        """Creates DuckDB connection with static S3 credentials."""
        config = StorageConnectionConfig(
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
            credential_type="static",
            access_key_id="test-key",
            secret_access_key="test-secret",
            endpoint="http://localhost:4566",
        )
        provider = StaticCredentialProvider(
            access_key_id="test-key",
            secret_access_key="test-secret",
        )

        conn = create_storage_connection(config, provider)

        # Verify connection is usable
        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1
        conn.close()

    @patch("adapters.duckdb.storage_connection._get_google_auth")
    def test_creates_connection_with_adc_credentials(self, mock_get_google_auth):
        """Creates DuckDB connection with ADC credentials."""
        mock_credentials = MagicMock()
        mock_credentials.token = "test-token"
        mock_credentials.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_credentials.expired = False

        mock_auth_default = MagicMock(return_value=(mock_credentials, "test-project"))
        mock_auth_request = MagicMock()
        mock_get_google_auth.return_value = (mock_auth_default, mock_auth_request)

        config = StorageConnectionConfig(
            bucket="bucket",
            prefix="prefix",
            region="us-central1",
            credential_type="adc",
        )
        provider = ADCCredentialProvider()

        conn = create_storage_connection(config, provider)

        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1
        conn.close()

    def test_configures_s3_endpoint_for_localstack(self):
        """S3 endpoint is configured when provided."""
        config = StorageConnectionConfig(
            bucket="bucket",
            prefix="prefix",
            region="us-east-1",
            credential_type="static",
            access_key_id="test",
            secret_access_key="test",
            endpoint="http://localhost:4566",
        )
        provider = StaticCredentialProvider(
            access_key_id="test",
            secret_access_key="test",
        )

        conn = create_storage_connection(config, provider)

        # Verify endpoint setting
        result = conn.execute("SELECT current_setting('s3_endpoint')").fetchone()
        assert result[0] == "localhost:4566"
        conn.close()
