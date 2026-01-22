from decimal import Decimal
from pathlib import Path

import duckdb

from domain.ports.analytics_repository import (
    AnalyticsRepository,
    FundMetadata,
    TickerPerformance,
    TickerDetails,
    TickerPriceAtDate,
)
from datetime import date


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
                total_return_pct,
                annualized_return_pct,
                volatility_pct,
                sharpe_ratio,
                vs_benchmark_pct
            FROM main_marts.fct_performance
            WHERE ticker IN ({placeholders})
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(query, tickers).fetchall()
            except duckdb.CatalogException:
                return []

        return [
            TickerPerformance(
                ticker=row[0],
                total_return_pct=Decimal(str(row[1])) if row[1] is not None else Decimal(0),
                annualized_return_pct=Decimal(str(row[2])) if row[2] is not None else Decimal(0),
                volatility_pct=Decimal(str(row[3])) if row[3] is not None else None,
                sharpe_ratio=Decimal(str(row[4])) if row[4] is not None else None,
                vs_benchmark_pct=Decimal(str(row[5])) if row[5] is not None else None,
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
                fund_name,
                asset_class,
                category,
                expense_ratio_pct,
                fund_inception_date
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

    def search_tickers(self, query: str, limit: int = 20) -> list[FundMetadata]:
        """Search for tickers by name or ticker symbol."""
        if not query:
            return []

        search_term = f"%{query.upper()}%"

        query_sql = """
            SELECT
                ticker,
                fund_name,
                asset_class,
                category,
                expense_ratio_pct,
                fund_inception_date
            FROM main_marts.dim_funds
            WHERE UPPER(ticker) LIKE ? OR UPPER(fund_name) LIKE ?
            ORDER BY
                CASE
                    WHEN UPPER(ticker) = ? THEN 1
                    WHEN UPPER(ticker) LIKE ? THEN 2
                    ELSE 3
                END,
                ticker
            LIMIT ?
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(
                    query_sql,
                    [search_term, search_term, query.upper(), f"{query.upper()}%", limit]
                ).fetchall()
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

    def get_all_securities(self) -> list[tuple[FundMetadata, TickerPerformance | None]]:
        """Retrieve all securities with their performance data."""
        query = """
            SELECT
                d.ticker,
                d.fund_name,
                d.asset_class,
                d.category,
                d.expense_ratio_pct,
                d.fund_inception_date,
                p.total_return_pct,
                p.annualized_return_pct,
                p.volatility_pct,
                p.sharpe_ratio,
                p.vs_benchmark_pct,
                p.total_return_1y_pct,
                p.return_vs_risk_free_1y_pct,
                p.return_vs_sp500_1y_pct,
                p.volatility_1y_pct,
                p.sharpe_ratio_1y,
                p.total_return_5y_pct,
                p.return_vs_risk_free_5y_pct,
                p.return_vs_sp500_5y_pct,
                p.volatility_5y_pct,
                p.sharpe_ratio_5y
            FROM main_marts.dim_funds d
            LEFT JOIN main_marts.fct_performance p ON d.ticker = p.ticker
            ORDER BY d.ticker
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(query).fetchall()
            except duckdb.CatalogException:
                return []

        securities = []
        for row in result:
            metadata = FundMetadata(
                ticker=row[0],
                name=row[1],
                asset_class=row[2],
                category=row[3],
                expense_ratio=Decimal(str(row[4])) if row[4] is not None else None,
                inception_date=row[5],
            )
            performance = None
            if row[6] is not None:
                performance = TickerPerformance(
                    ticker=row[0],
                    total_return_pct=Decimal(str(row[6])) if row[6] is not None else Decimal(0),
                    annualized_return_pct=Decimal(str(row[7])) if row[7] is not None else Decimal(0),
                    volatility_pct=Decimal(str(row[8])) if row[8] is not None else None,
                    sharpe_ratio=Decimal(str(row[9])) if row[9] is not None else None,
                    vs_benchmark_pct=Decimal(str(row[10])) if row[10] is not None else None,
                    # 1-Year metrics
                    total_return_1y_pct=Decimal(str(row[11])) if row[11] is not None else None,
                    return_vs_risk_free_1y_pct=Decimal(str(row[12])) if row[12] is not None else None,
                    return_vs_sp500_1y_pct=Decimal(str(row[13])) if row[13] is not None else None,
                    volatility_1y_pct=Decimal(str(row[14])) if row[14] is not None else None,
                    sharpe_ratio_1y=Decimal(str(row[15])) if row[15] is not None else None,
                    # 5-Year metrics
                    total_return_5y_pct=Decimal(str(row[16])) if row[16] is not None else None,
                    return_vs_risk_free_5y_pct=Decimal(str(row[17])) if row[17] is not None else None,
                    return_vs_sp500_5y_pct=Decimal(str(row[18])) if row[18] is not None else None,
                    volatility_5y_pct=Decimal(str(row[19])) if row[19] is not None else None,
                    sharpe_ratio_5y=Decimal(str(row[20])) if row[20] is not None else None,
                )
            securities.append((metadata, performance))

        return securities

    def get_ticker_details(self, ticker: str) -> TickerDetails | None:
        """Get detailed ticker info including latest price for holding creation."""
        query = """
            WITH latest_price AS (
                SELECT
                    p.price,
                    p.as_of_date
                FROM main_marts.fact_price_daily p
                JOIN main_marts.dim_security s ON p.security_id = s.security_id
                WHERE UPPER(s.ticker) = UPPER(?)
                ORDER BY p.as_of_date DESC
                LIMIT 1
            )
            SELECT
                d.ticker,
                d.fund_name,
                d.asset_class,
                d.sector,
                d.category,
                lp.price,
                lp.as_of_date
            FROM main_marts.dim_funds d
            LEFT JOIN latest_price lp ON 1=1
            WHERE UPPER(d.ticker) = UPPER(?)
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(query, [ticker, ticker]).fetchone()
            except duckdb.CatalogException:
                return None

        if not result:
            return None

        return TickerDetails(
            ticker=result[0],
            name=result[1],
            asset_class=result[2],
            sector=result[3],
            category=result[4],
            latest_price=Decimal(str(result[5])) if result[5] is not None else None,
            latest_price_date=result[6],
        )

    def get_price_for_date(self, ticker: str, price_date: date) -> TickerPriceAtDate | None:
        """Get the price for a ticker at or before a specific date."""
        query = """
            SELECT
                s.ticker,
                p.as_of_date,
                p.price
            FROM main_marts.fact_price_daily p
            JOIN main_marts.dim_security s ON p.security_id = s.security_id
            WHERE UPPER(s.ticker) = UPPER(?)
              AND p.as_of_date <= ?
            ORDER BY p.as_of_date DESC
            LIMIT 1
        """

        with self._get_connection() as conn:
            try:
                result = conn.execute(query, [ticker, price_date]).fetchone()
            except duckdb.CatalogException:
                return None

        if not result:
            return None

        return TickerPriceAtDate(
            ticker=result[0],
            price_date=result[1],
            price=Decimal(str(result[2])),
        )
