"""
Storage connection factory for cloud object storage.

Provides a DuckDB connection configured to read Parquet files from
S3-compatible or GCS storage using the httpfs extension.

Supports two credential modes:
- Static: Traditional access key/secret key (for LocalStack, S3)
- ADC: Google Application Default Credentials (for GCS in Cloud Run)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

import duckdb

# Type checking imports
if TYPE_CHECKING:
    from google.auth.credentials import Credentials as GoogleCredentials


def _get_google_auth():
    """Lazy import for google.auth to avoid hard dependency."""
    try:
        from google.auth import default as google_auth_default
        from google.auth.transport.requests import Request as GoogleAuthRequest

        return google_auth_default, GoogleAuthRequest
    except ImportError:
        return None, None


@dataclass(frozen=True)
class Credentials:
    """Container for storage credentials."""

    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    token: Optional[str] = None


class CredentialProvider(ABC):
    """Abstract base class for credential providers."""

    @abstractmethod
    def get_credentials(self) -> Credentials:
        """Get current credentials, refreshing if necessary."""
        pass

    @abstractmethod
    def needs_refresh(self) -> bool:
        """Check if credentials need to be refreshed."""
        pass


class StaticCredentialProvider(CredentialProvider):
    """Provides static credentials that never expire.

    Used for LocalStack development and traditional S3 access.
    """

    def __init__(self, access_key_id: str, secret_access_key: str) -> None:
        self._credentials = Credentials(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
        )

    def get_credentials(self) -> Credentials:
        """Return static credentials."""
        return self._credentials

    def needs_refresh(self) -> bool:
        """Static credentials never need refresh."""
        return False


class ADCCredentialProvider(CredentialProvider):
    """Provides Google Cloud Application Default Credentials.

    Implements lazy initialization and automatic token refresh when
    tokens are about to expire.
    """

    def __init__(self, refresh_threshold_minutes: int = 5) -> None:
        """Initialize ADC provider.

        Args:
            refresh_threshold_minutes: Refresh token if it expires within
                this many minutes. Default is 5 minutes.
        """
        self._refresh_threshold = timedelta(minutes=refresh_threshold_minutes)
        self._credentials: Optional["GoogleCredentials"] = None
        self._project: Optional[str] = None
        self._google_auth_default = None
        self._google_auth_request = None

    def _ensure_google_auth(self) -> None:
        """Ensure google.auth is available, raising ImportError if not."""
        if self._google_auth_default is None:
            google_auth_default, google_auth_request = _get_google_auth()
            if google_auth_default is None:
                raise ImportError(
                    "google-auth package is required for ADC credentials. "
                    "Install with: pip install google-auth"
                )
            self._google_auth_default = google_auth_default
            self._google_auth_request = google_auth_request

    def get_credentials(self) -> Credentials:
        """Get credentials, initializing or refreshing as needed."""
        self._ensure_google_auth()

        if self._credentials is None:
            self._credentials, self._project = self._google_auth_default()

        # Check if refresh is needed
        if self._credentials.expired or self.needs_refresh():
            self._credentials.refresh(self._google_auth_request())

        return Credentials(token=self._credentials.token)

    def needs_refresh(self) -> bool:
        """Check if token is expired or expiring soon."""
        if self._credentials is None:
            return False  # Not initialized yet

        if self._credentials.expiry is None:
            return False  # Some credentials don't have expiry

        time_remaining = self._credentials.expiry - datetime.now(timezone.utc)
        return time_remaining < self._refresh_threshold


@dataclass(frozen=True)
class StorageConnectionConfig:
    """Configuration for cloud storage connections."""

    bucket: str
    prefix: str
    region: str
    credential_type: str  # "static" or "adc"

    # Optional fields
    endpoint: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    use_gcs_prefix: bool = False

    def get_parquet_path(self, namespace: str, table_name: str) -> str:
        """Get the path to a Parquet file.

        Args:
            namespace: Schema namespace (e.g., "marts", "intermediate")
            table_name: Name of the table

        Returns:
            Full path to the Parquet file (s3:// or gs://)
        """
        prefix = "gs://" if self.use_gcs_prefix else "s3://"
        return f"{prefix}{self.bucket}/{self.prefix}/{namespace}/{table_name}.parquet"


def _escape_sql_string(value: str) -> str:
    """Escape a string for use in DuckDB SET statements."""
    return value.replace("'", "''")


def read_parquet_sql(path: str) -> str:
    """Generate SQL for reading a Parquet file.

    Args:
        path: Full path to Parquet file (s3:// or gs://)

    Returns:
        SQL expression for reading the Parquet file
    """
    return f"read_parquet('{path}')"


def create_storage_connection(
    config: StorageConnectionConfig,
    credential_provider: CredentialProvider,
) -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection configured for cloud storage reads.

    Args:
        config: Storage configuration
        credential_provider: Provider for credentials

    Returns:
        Configured DuckDB connection (in-memory)
    """
    conn = duckdb.connect(":memory:")

    # Install and load httpfs extension
    conn.execute("INSTALL httpfs")
    conn.execute("LOAD httpfs")

    # Get credentials
    creds = credential_provider.get_credentials()

    # Configure based on credential type
    if config.credential_type == "static":
        # Static credentials for S3/LocalStack
        access_key = _escape_sql_string(creds.access_key_id or "")
        secret_key = _escape_sql_string(creds.secret_access_key or "")
        region = _escape_sql_string(config.region)

        conn.execute(f"SET s3_access_key_id = '{access_key}'")
        conn.execute(f"SET s3_secret_access_key = '{secret_key}'")
        conn.execute(f"SET s3_region = '{region}'")

    elif config.credential_type == "adc":
        # ADC credentials for GCS
        # For GCS with httpfs, we use the token as a bearer token
        if creds.token:
            token = _escape_sql_string(creds.token)
            conn.execute(f"SET s3_session_token = '{token}'")

        region = _escape_sql_string(config.region)
        conn.execute(f"SET s3_region = '{region}'")

    # Configure endpoint if provided (for LocalStack)
    if config.endpoint:
        # Strip protocol for DuckDB endpoint setting
        endpoint = config.endpoint.replace("http://", "").replace("https://", "")
        endpoint = _escape_sql_string(endpoint)
        conn.execute(f"SET s3_endpoint = '{endpoint}'")
        conn.execute("SET s3_url_style = 'path'")

        # Determine SSL based on original endpoint
        use_ssl = config.endpoint.startswith("https")
        conn.execute(f"SET s3_use_ssl = {str(use_ssl).lower()}")

    return conn
