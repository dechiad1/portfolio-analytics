from decimal import Decimal
from pathlib import Path

import duckdb

from domain.ports.analytics_repository import (
    AnalyticsRepository,
    FundMetadata,
    TickerPerformance,
)


class DuckDBAnalyticsRepository(AnalyticsRepository):
    """DuckDB implementation of AnalyticsRepository for reading from data warehouse."""

    def __init__(self, database_path: str) -> None:
        self._database_path = Path(database_path)
        if not self._database_path.exists():
            raise FileNotFoundError(
                f"DuckDB database not found at {self._database_path}"
            )

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a read-only connection to DuckDB."""
        return duckdb.connect(str(self._database_path), read_only=True)

    def get_performance_for_tickers(
        self, tickers: list[str]
    ) -> list[TickerPerformance]:
        """Retrieve performance data for the given tickers from fct_performance."""
        if not tickers:
            return []

        placeholders = ", ".join(["?" for _ in tickers])

        query = f"""
            SELECT
                ticker,
                date,
                daily_return,
                cumulative_return,
                volatility
            FROM main_marts.fct_performance
            WHERE ticker IN ({placeholders})
            ORDER BY ticker, date DESC
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(query, tickers).fetchall()
            except duckdb.CatalogException:
                return []

        return [
            TickerPerformance(
                ticker=row[0],
                date=row[1],
                daily_return=Decimal(str(row[2])) if row[2] is not None else Decimal(0),
                cumulative_return=(
                    Decimal(str(row[3])) if row[3] is not None else Decimal(0)
                ),
                volatility=Decimal(str(row[4])) if row[4] is not None else None,
            )
            for row in result
        ]

    def get_fund_metadata_for_tickers(self, tickers: list[str]) -> list[FundMetadata]:
        """Retrieve fund metadata for the given tickers from dim_funds."""
        if not tickers:
            return []

        placeholders = ", ".join(["?" for _ in tickers])

        query = f"""
            SELECT
                ticker,
                name,
                asset_class,
                category,
                expense_ratio,
                inception_date
            FROM main_marts.dim_funds
            WHERE ticker IN ({placeholders})
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(query, tickers).fetchall()
            except duckdb.CatalogException:
                return []

        return [
            FundMetadata(
                ticker=row[0],
                name=row[1],
                asset_class=row[2],
                category=row[3],
                expense_ratio=(
                    Decimal(str(row[4])) if row[4] is not None else None
                ),
                inception_date=row[5],
            )
            for row in result
        ]
