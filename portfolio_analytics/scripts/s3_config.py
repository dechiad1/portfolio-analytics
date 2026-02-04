"""
S3-compatible storage configuration.

Works with any S3-compatible storage provider:
- AWS S3 (default)
- Google Cloud Storage (via S3 compatibility)
- MinIO (local development)
- LocalStack (testing)

Configuration is read from environment variables:
- S3_ENDPOINT: Custom endpoint URL (empty for AWS S3)
- S3_ACCESS_KEY_ID: Access key
- S3_SECRET_ACCESS_KEY: Secret key
- S3_BUCKET: Bucket name
- S3_PREFIX: Path prefix within bucket (default: "portfolio-analytics")
- S3_REGION: AWS region (default: "us-east-1")
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class S3Config:
    """S3-compatible storage configuration."""

    endpoint: Optional[str]
    access_key_id: str
    secret_access_key: str
    bucket: str
    prefix: str
    region: str

    @classmethod
    def from_env(cls) -> "S3Config":
        """Load S3 configuration from environment variables."""
        endpoint = os.getenv("S3_ENDPOINT", "").strip() or None
        access_key_id = os.getenv("S3_ACCESS_KEY_ID", "")
        secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY", "")
        bucket = os.getenv("S3_BUCKET", "")
        prefix = os.getenv("S3_PREFIX", "portfolio-analytics")
        region = os.getenv("S3_REGION", "us-east-1")

        return cls(
            endpoint=endpoint,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            bucket=bucket,
            prefix=prefix,
            region=region,
        )

    def is_configured(self) -> bool:
        """Check if S3 is properly configured."""
        return bool(self.access_key_id and self.secret_access_key and self.bucket)

    def get_raw_path(self, table_name: str) -> str:
        """Get the S3 path for a raw table (Parquet format)."""
        return f"s3://{self.bucket}/{self.prefix}/raw/{table_name}.parquet"

    def get_iceberg_path(self, table_name: str) -> str:
        """Get the S3 path for an Iceberg table."""
        return f"s3://{self.bucket}/{self.prefix}/iceberg/marts/{table_name}"

    def get_duckdb_s3_config(self) -> dict:
        """Get DuckDB S3 configuration for httpfs extension."""
        config = {
            "s3_access_key_id": self.access_key_id,
            "s3_secret_access_key": self.secret_access_key,
            "s3_region": self.region,
        }
        if self.endpoint:
            config["s3_endpoint"] = self.endpoint
            config["s3_url_style"] = "path"
            config["s3_use_ssl"] = "true" if self.endpoint.startswith("https") else "false"
        return config

    def get_fsspec_config(self) -> dict:
        """Get configuration for s3fs/fsspec."""
        config = {
            "key": self.access_key_id,
            "secret": self.secret_access_key,
        }
        if self.endpoint:
            config["client_kwargs"] = {"endpoint_url": self.endpoint}
        return config


def get_s3_config() -> Optional[S3Config]:
    """
    Get S3 configuration if available.

    Returns:
        S3Config if properly configured, None otherwise.
    """
    config = S3Config.from_env()
    if config.is_configured():
        return config
    return None
