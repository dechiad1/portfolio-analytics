import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class PostgresConfig(BaseModel):
    """PostgreSQL database configuration."""

    host: str
    port: int
    database: str
    user: str
    password: str


class DuckDBConfig(BaseModel):
    """DuckDB configuration."""

    path: str


class DatabaseConfig(BaseModel):
    """Database configuration container."""

    postgres: PostgresConfig
    duckdb: DuckDBConfig


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str
    port: int
    cors_origins: list[str]


class AppConfig(BaseModel):
    """Application configuration."""

    database: DatabaseConfig
    server: ServerConfig


def _resolve_env_vars(value: Any) -> Any:
    """Recursively resolve environment variables in config values."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.environ.get(env_var, "")
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


@lru_cache
def load_config() -> AppConfig:
    """Load configuration from YAML file based on environment."""
    env = os.environ.get("APP_ENV", "local")
    config_path = Path(__file__).parent / "config" / f"{env}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    resolved_config = _resolve_env_vars(raw_config)
    return AppConfig(**resolved_config)


# Singleton instances for repositories and services
_postgres_pool = None
_session_repository = None
_holding_repository = None
_analytics_repository = None
_session_service = None
_holding_service = None
_compute_analytics_command = None


def get_postgres_pool():
    """Get or create PostgreSQL connection pool."""
    global _postgres_pool
    if _postgres_pool is None:
        from adapters.postgres.connection import PostgresConnectionPool

        config = load_config()
        _postgres_pool = PostgresConnectionPool(
            host=config.database.postgres.host,
            port=config.database.postgres.port,
            database=config.database.postgres.database,
            user=config.database.postgres.user,
            password=config.database.postgres.password,
        )
        _postgres_pool.initialize_schema()
    return _postgres_pool


def get_session_repository():
    """Get or create SessionRepository instance."""
    global _session_repository
    if _session_repository is None:
        from adapters.postgres.session_repository import PostgresSessionRepository

        _session_repository = PostgresSessionRepository(get_postgres_pool())
    return _session_repository


def get_holding_repository():
    """Get or create HoldingRepository instance."""
    global _holding_repository
    if _holding_repository is None:
        from adapters.postgres.holding_repository import PostgresHoldingRepository

        _holding_repository = PostgresHoldingRepository(get_postgres_pool())
    return _holding_repository


def get_analytics_repository():
    """Get or create AnalyticsRepository instance."""
    global _analytics_repository
    if _analytics_repository is None:
        from adapters.duckdb.analytics_repository import DuckDBAnalyticsRepository

        config = load_config()
        db_path = Path(__file__).parent / config.database.duckdb.path
        _analytics_repository = DuckDBAnalyticsRepository(str(db_path))
    return _analytics_repository


def get_session_service():
    """Get or create SessionService instance for FastAPI dependency injection."""
    global _session_service
    if _session_service is None:
        from domain.services.session_service import SessionService

        _session_service = SessionService(get_session_repository())
    return _session_service


def get_holding_service():
    """Get or create HoldingService instance for FastAPI dependency injection."""
    global _holding_service
    if _holding_service is None:
        from domain.services.holding_service import HoldingService

        _holding_service = HoldingService(get_holding_repository())
    return _holding_service


def get_compute_analytics_command():
    """Get or create ComputeAnalyticsCommand instance for FastAPI dependency injection."""
    global _compute_analytics_command
    if _compute_analytics_command is None:
        from domain.commands.compute_analytics import ComputeAnalyticsCommand

        _compute_analytics_command = ComputeAnalyticsCommand(
            holding_repository=get_holding_repository(),
            analytics_repository=get_analytics_repository(),
        )
    return _compute_analytics_command


def reset_dependencies() -> None:
    """Reset all singleton instances. Useful for testing."""
    global _postgres_pool, _session_repository, _holding_repository
    global _analytics_repository, _session_service, _holding_service
    global _compute_analytics_command

    if _postgres_pool is not None:
        _postgres_pool.close()

    _postgres_pool = None
    _session_repository = None
    _holding_repository = None
    _analytics_repository = None
    _session_service = None
    _holding_service = None
    _compute_analytics_command = None
