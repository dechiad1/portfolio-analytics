"""DuckDB implementation of SimulationParamsRepository."""

import duckdb
import numpy as np
from numpy.typing import NDArray

from domain.ports.simulation_params_repository import (
    SimulationParamsRepository,
    SecuritySimParams,
)
from .base_repository import BaseDuckDBRepository


class DuckDBSimulationParamsRepository(BaseDuckDBRepository, SimulationParamsRepository):
    """DuckDB implementation for fetching simulation parameters.

    Supports two modes:
    - Local file mode: Reads from a local DuckDB file
    - Iceberg mode: Reads from Iceberg tables on S3 via DuckDB's Iceberg extension

    Both modes use identical SQL queries - the _table_ref() method from the base class
    returns the appropriate table reference for each mode.
    """

    def get_security_params(self, tickers: list[str]) -> list[SecuritySimParams]:
        """Fetch mu and volatility for the given securities."""
        if not tickers:
            return []

        placeholders = ", ".join(["?" for _ in tickers])

        hmu_ref = self._table_ref("security_historical_mu")
        fmu_ref = self._table_ref("security_forward_mu")
        vol_ref = self._table_ref("security_volatility")

        # iceberg_scan() returns a table expression that works directly in JOINs
        query = f"""
            SELECT
                hmu.ticker,
                hmu.annualized_mu as historical_mu,
                fmu.forward_mu,
                vol.annualized_volatility as volatility
            FROM {hmu_ref} hmu
            LEFT JOIN {fmu_ref} fmu ON hmu.ticker = fmu.ticker
            LEFT JOIN {vol_ref} vol ON hmu.ticker = vol.ticker
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
        table_ref = self._table_ref("int_daily_returns", "intermediate")

        query = f"""
            SELECT
                ticker,
                date,
                daily_return
            FROM {table_ref}
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
