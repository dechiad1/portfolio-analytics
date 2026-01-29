import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

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


class AuthConfig(BaseModel):
    """Authentication configuration."""

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    token_expiry_hours: int = 24


class OAuthConfig(BaseModel):
    """OAuth configuration."""

    issuer_url: str
    client_id: str
    client_secret: str
    redirect_uri: str


class LLMConfig(BaseModel):
    """LLM configuration."""

    anthropic_api_key: str
    model: str = "claude-sonnet-4-20250514"


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str
    port: int
    cors_origins: list[str]
    frontend_url: str = "http://localhost:3001"


class AppConfig(BaseModel):
    """Application configuration."""

    database: DatabaseConfig
    server: ServerConfig
    auth: AuthConfig
    llm: LLMConfig
    oauth: Optional[OAuthConfig] = None


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
_holding_repository = None
_user_repository = None
_portfolio_repository = None
_analytics_repository = None
_holding_service = None
_auth_service = None
_oauth_provider = None
_oauth_service = None
_portfolio_service = None
_llm_repository = None
_risk_analysis_service = None
_compute_analytics_command = None
_ticker_validator = None
_ticker_repository = None
_ticker_service = None
_simulation_params_repository = None
_simulation_service = None
_simulation_repository = None
_portfolio_builder_service = None
_create_portfolio_command = None
_unit_of_work = None
_portfolio_builder_repository = None
_risk_analysis_repository = None


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
    return _postgres_pool


def get_holding_repository():
    """Get or create HoldingRepository instance."""
    global _holding_repository
    if _holding_repository is None:
        from adapters.postgres.holding_repository import PostgresHoldingRepository

        _holding_repository = PostgresHoldingRepository(get_postgres_pool())
    return _holding_repository


def get_user_repository():
    """Get or create UserRepository instance."""
    global _user_repository
    if _user_repository is None:
        from adapters.postgres.user_repository import PostgresUserRepository

        _user_repository = PostgresUserRepository(get_postgres_pool())
    return _user_repository


def get_portfolio_repository():
    """Get or create PortfolioRepository instance."""
    global _portfolio_repository
    if _portfolio_repository is None:
        from adapters.postgres.portfolio_repository import PostgresPortfolioRepository

        _portfolio_repository = PostgresPortfolioRepository(get_postgres_pool())
    return _portfolio_repository


def get_analytics_repository():
    """Get or create AnalyticsRepository instance."""
    global _analytics_repository
    if _analytics_repository is None:
        from adapters.duckdb.analytics_repository import DuckDBAnalyticsRepository

        config = load_config()
        db_path = Path(__file__).parent / config.database.duckdb.path
        _analytics_repository = DuckDBAnalyticsRepository(str(db_path))
    return _analytics_repository


def get_holding_service():
    """Get or create HoldingService instance for FastAPI dependency injection."""
    global _holding_service
    if _holding_service is None:
        from domain.services.holding_service import HoldingService

        _holding_service = HoldingService(get_holding_repository())
    return _holding_service


def get_auth_service():
    """Get or create AuthService instance for FastAPI dependency injection."""
    global _auth_service
    if _auth_service is None:
        from domain.services.auth_service import AuthService

        config = load_config()
        _auth_service = AuthService(
            user_repository=get_user_repository(),
            jwt_secret=config.auth.jwt_secret,
            jwt_algorithm=config.auth.jwt_algorithm,
            token_expiry_hours=config.auth.token_expiry_hours,
        )
    return _auth_service


def get_oauth_provider():
    """Get or create OAuth provider instance."""
    global _oauth_provider
    if _oauth_provider is None:
        from adapters.oauth.mock_oauth_provider import MockOAuth2Provider

        config = load_config()
        if config.oauth is None:
            raise RuntimeError("OAuth not configured")

        _oauth_provider = MockOAuth2Provider(
            issuer_url=config.oauth.issuer_url,
            client_id=config.oauth.client_id,
            client_secret=config.oauth.client_secret,
            redirect_uri=config.oauth.redirect_uri,
        )
    return _oauth_provider


def get_oauth_service():
    """Get or create OAuthService instance for FastAPI dependency injection."""
    global _oauth_service
    if _oauth_service is None:
        from domain.services.oauth_service import OAuthService

        config = load_config()
        _oauth_service = OAuthService(
            user_repository=get_user_repository(),
            oauth_provider=get_oauth_provider(),
            jwt_secret=config.auth.jwt_secret,
            jwt_algorithm=config.auth.jwt_algorithm,
            token_expiry_hours=config.auth.token_expiry_hours,
        )
    return _oauth_service


def get_portfolio_service():
    """Get or create PortfolioService instance for FastAPI dependency injection."""
    global _portfolio_service
    if _portfolio_service is None:
        from domain.services.portfolio_service import PortfolioService

        _portfolio_service = PortfolioService(
            portfolio_repository=get_portfolio_repository(),
            holding_repository=get_holding_repository(),
        )
    return _portfolio_service


def get_llm_repository():
    """Get or create LLMRepository instance. Returns None if API key not configured."""
    global _llm_repository
    if _llm_repository is None:
        config = load_config()
        if not config.llm.anthropic_api_key:
            return None

        from adapters.llm.anthropic_repository import AnthropicLLMRepository

        _llm_repository = AnthropicLLMRepository(
            api_key=config.llm.anthropic_api_key,
            model=config.llm.model,
        )
    return _llm_repository


def get_risk_analysis_repository():
    """Get or create RiskAnalysisRepository instance."""
    global _risk_analysis_repository
    if _risk_analysis_repository is None:
        from adapters.postgres.risk_analysis_repository import PostgresRiskAnalysisRepository

        _risk_analysis_repository = PostgresRiskAnalysisRepository(get_postgres_pool())
    return _risk_analysis_repository


def get_risk_analysis_service():
    """Get or create RiskAnalysisService instance for FastAPI dependency injection."""
    global _risk_analysis_service
    if _risk_analysis_service is None:
        from domain.services.risk_analysis_service import RiskAnalysisService

        _risk_analysis_service = RiskAnalysisService(
            llm_repository=get_llm_repository(),
            portfolio_repository=get_portfolio_repository(),
            holding_repository=get_holding_repository(),
            risk_analysis_repository=get_risk_analysis_repository(),
        )
    return _risk_analysis_service


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


def get_ticker_validator():
    """Get or create TickerValidator instance."""
    global _ticker_validator
    if _ticker_validator is None:
        from adapters.yfinance.ticker_validator import YFinanceTickerValidator

        _ticker_validator = YFinanceTickerValidator()
    return _ticker_validator


def get_ticker_repository():
    """Get or create TickerRepository instance."""
    global _ticker_repository
    if _ticker_repository is None:
        from adapters.postgres.ticker_repository import PostgresTickerRepository

        _ticker_repository = PostgresTickerRepository(get_postgres_pool())
    return _ticker_repository


def get_ticker_service():
    """Get or create TickerService instance for FastAPI dependency injection."""
    global _ticker_service
    if _ticker_service is None:
        from domain.services.ticker_service import TickerService

        _ticker_service = TickerService(
            validator=get_ticker_validator(),
            repository=get_ticker_repository(),
        )
    return _ticker_service


def get_simulation_params_repository():
    """Get or create SimulationParamsRepository instance."""
    global _simulation_params_repository
    if _simulation_params_repository is None:
        from adapters.duckdb.simulation_params_repository import (
            DuckDBSimulationParamsRepository,
        )

        config = load_config()
        db_path = Path(__file__).parent / config.database.duckdb.path
        _simulation_params_repository = DuckDBSimulationParamsRepository(str(db_path))
    return _simulation_params_repository


def get_simulation_service():
    """Get or create SimulationService instance for FastAPI dependency injection."""
    global _simulation_service
    if _simulation_service is None:
        from domain.services.simulation_service import SimulationService

        _simulation_service = SimulationService(
            portfolio_repository=get_portfolio_repository(),
            holding_repository=get_holding_repository(),
            simulation_params_repository=get_simulation_params_repository(),
        )
    return _simulation_service


def get_simulation_repository():
    """Get or create SimulationRepository instance."""
    global _simulation_repository
    if _simulation_repository is None:
        from adapters.postgres.simulation_repository import PostgresSimulationRepository

        _simulation_repository = PostgresSimulationRepository(get_postgres_pool())
    return _simulation_repository


def get_unit_of_work():
    """Get or create UnitOfWork instance."""
    global _unit_of_work
    if _unit_of_work is None:
        from adapters.postgres.unit_of_work import PostgresUnitOfWork

        _unit_of_work = PostgresUnitOfWork(get_postgres_pool())
    return _unit_of_work


def get_portfolio_builder_repository():
    """Get or create PortfolioBuilderRepository instance."""
    global _portfolio_builder_repository
    if _portfolio_builder_repository is None:
        from adapters.postgres.portfolio_builder_repository import (
            PostgresPortfolioBuilderRepository,
        )

        _portfolio_builder_repository = PostgresPortfolioBuilderRepository()
    return _portfolio_builder_repository


def get_portfolio_builder_service():
    """Get or create PortfolioBuilderService instance."""
    global _portfolio_builder_service
    if _portfolio_builder_service is None:
        from domain.services.portfolio_builder_service import PortfolioBuilderService

        _portfolio_builder_service = PortfolioBuilderService(
            ticker_repository=get_ticker_repository(),
            llm_repository=get_llm_repository(),
        )
    return _portfolio_builder_service


def get_create_portfolio_command():
    """Get or create CreatePortfolioWithHoldingsCommand instance."""
    global _create_portfolio_command
    if _create_portfolio_command is None:
        from domain.commands.create_portfolio_with_holdings import (
            CreatePortfolioWithHoldingsCommand,
        )

        _create_portfolio_command = CreatePortfolioWithHoldingsCommand(
            unit_of_work=get_unit_of_work(),
            portfolio_builder_repository=get_portfolio_builder_repository(),
            analytics_repository=get_analytics_repository(),
        )
    return _create_portfolio_command


def reset_dependencies() -> None:
    """Reset all singleton instances. Useful for testing."""
    global _postgres_pool, _holding_repository
    global _user_repository, _portfolio_repository
    global _analytics_repository, _holding_service
    global _auth_service, _oauth_provider, _oauth_service, _portfolio_service
    global _llm_repository, _risk_analysis_service, _risk_analysis_repository
    global _compute_analytics_command
    global _ticker_validator, _ticker_repository, _ticker_service
    global _simulation_params_repository, _simulation_service
    global _simulation_repository, _portfolio_builder_service
    global _create_portfolio_command, _unit_of_work, _portfolio_builder_repository

    if _postgres_pool is not None:
        _postgres_pool.close()

    _postgres_pool = None
    _holding_repository = None
    _user_repository = None
    _portfolio_repository = None
    _analytics_repository = None
    _holding_service = None
    _auth_service = None
    _oauth_provider = None
    _oauth_service = None
    _portfolio_service = None
    _llm_repository = None
    _risk_analysis_service = None
    _risk_analysis_repository = None
    _compute_analytics_command = None
    _ticker_validator = None
    _ticker_repository = None
    _ticker_service = None
    _simulation_params_repository = None
    _simulation_service = None
    _simulation_repository = None
    _portfolio_builder_service = None
    _create_portfolio_command = None
    _unit_of_work = None
    _portfolio_builder_repository = None
