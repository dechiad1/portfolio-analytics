"""DuckDB implementation of SimulationParamsRepository."""

from pathlib import Path
from typing import Optional

import duckdb
import numpy as np
from numpy.typing import NDArray

from domain.ports.simulation_params_repository import (
    SimulationParamsRepository,
    SecuritySimParams,
)


class DuckDBSimulationParamsRepository(SimulationParamsRepository):
    """DuckDB implementation for fetching simulation parameters.

    Supports two modes:
    - Local file mode: Reads from a local DuckDB file
    - Iceberg mode: Reads from Iceberg tables on S3 via DuckDB's Iceberg extension
    """

    def __init__(
        self,
        database_path: Optional[str] = None,
        iceberg_config: Optional["IcebergConnectionConfig"] = None,  # noqa: F821
    ) -> None:
        """
        Initialize the simulation params repository.

        Args:
            database_path: Path to local DuckDB file (for local mode)
            iceberg_config: Configuration for Iceberg mode (mutually exclusive with database_path)
        """
        self._database_path: Optional[Path] = None
        self._iceberg_config = iceberg_config

        if iceberg_config is not None:
            # Iceberg mode
            self._mode = "iceberg"
        elif database_path is not None:
            # Local file mode
            self._mode = "local"
            self._database_path = Path(database_path)
            if not self._database_path.exists():
                raise FileNotFoundError(
                    f"DuckDB database not found at {self._database_path}"
                )
        else:
            raise ValueError("Either database_path or iceberg_config must be provided")

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a connection to DuckDB."""
        if self._mode == "iceberg":
            from .iceberg_connection import create_iceberg_connection
            return create_iceberg_connection(self._iceberg_config)
        else:
            return duckdb.connect(str(self._database_path), read_only=True)

    def _table_ref(self, table_name: str, schema: str = "marts") -> str:
        """
        Get the table reference for a given table name.

        Args:
            table_name: Name of the table
            schema: Schema/namespace (marts, intermediate)

        Returns:
            Table reference string for SQL queries
        """
        if self._mode == "iceberg":
            from .iceberg_connection import iceberg_scan_sql
            # For Iceberg, use the config to build the table path
            namespace = "marts" if schema == "marts" else schema.replace("main_", "")
            table_path = self._iceberg_config.get_table_path(namespace, table_name)
            return iceberg_scan_sql(table_path)
        else:
            duckdb_schema = f"main_{schema}" if not schema.startswith("main_") else schema
            return f"{duckdb_schema}.{table_name}"

    def get_security_params(self, tickers: list[str]) -> list[SecuritySimParams]:
        """Fetch mu and volatility for the given securities."""
        if not tickers:
            return []

        placeholders = ", ".join(["?" for _ in tickers])

        hmu_ref = self._table_ref("security_historical_mu")
        fmu_ref = self._table_ref("security_forward_mu")
        vol_ref = self._table_ref("security_volatility")

        if self._mode == "iceberg":
            query = f"""
                WITH hmu AS (SELECT * FROM {hmu_ref}),
                     fmu AS (SELECT * FROM {fmu_ref}),
                     vol AS (SELECT * FROM {vol_ref})
                SELECT
                    hmu.ticker,
                    hmu.annualized_mu as historical_mu,
                    fmu.forward_mu,
                    vol.annualized_volatility as volatility
                FROM hmu
                LEFT JOIN fmu ON hmu.ticker = fmu.ticker
                LEFT JOIN vol ON hmu.ticker = vol.ticker
                WHERE hmu.ticker IN ({placeholders})
            """
        else:
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
