"""DuckDB implementation of SimulationParamsRepository."""

from pathlib import Path

import duckdb
import numpy as np
from numpy.typing import NDArray

from domain.ports.simulation_params_repository import (
    SimulationParamsRepository,
    SecuritySimParams,
)


class DuckDBSimulationParamsRepository(SimulationParamsRepository):
    """DuckDB implementation for fetching simulation parameters."""

    def __init__(self, database_path: str) -> None:
        self._database_path = Path(database_path)
        if not self._database_path.exists():
            raise FileNotFoundError(
                f"DuckDB database not found at {self._database_path}"
            )

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a read-only connection to DuckDB."""
        return duckdb.connect(str(self._database_path), read_only=True)

    def get_security_params(self, tickers: list[str]) -> list[SecuritySimParams]:
        """Fetch mu and volatility for the given securities."""
        if not tickers:
            return []

        placeholders = ", ".join(["?" for _ in tickers])

        query = f"""
            SELECT
                hmu.ticker,
                hmu.annualized_mu as historical_mu,
                fmu.forward_mu,
                vol.annualized_volatility as volatility
            FROM main_marts.security_historical_mu hmu
            LEFT JOIN main_marts.security_forward_mu fmu ON hmu.ticker = fmu.ticker
            LEFT JOIN main_marts.security_volatility vol ON hmu.ticker = vol.ticker
            WHERE hmu.ticker IN ({placeholders})
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(query, tickers).fetchall()
            except duckdb.CatalogException:
                return []

        return [
            SecuritySimParams(
                ticker=row[0],
                historical_mu=float(row[1]) if row[1] is not None else None,
                forward_mu=float(row[2]) if row[2] is not None else None,
                volatility=float(row[3]) if row[3] is not None else None,
            )
            for row in result
        ]

    def get_historical_returns(
        self, tickers: list[str]
    ) -> dict[str, NDArray[np.floating]]:
        """Fetch historical daily returns for correlation calculation."""
        if not tickers:
            return {}

        placeholders = ", ".join(["?" for _ in tickers])

        query = f"""
            SELECT
                ticker,
                date,
                daily_return
            FROM main_intermediate.int_daily_returns
            WHERE ticker IN ({placeholders})
              AND daily_return IS NOT NULL
            ORDER BY ticker, date
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(query, tickers).fetchall()
            except duckdb.CatalogException:
                return {}

        # Group returns by ticker
        returns_by_ticker: dict[str, list[float]] = {t: [] for t in tickers}
        for row in result:
            ticker, _, daily_return = row
            if ticker in returns_by_ticker:
                returns_by_ticker[ticker].append(float(daily_return))

        return {
            ticker: np.array(returns, dtype=np.float64)
            for ticker, returns in returns_by_ticker.items()
            if returns
        }
