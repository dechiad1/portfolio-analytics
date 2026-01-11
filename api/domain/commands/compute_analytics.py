from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from domain.models.holding import Holding
from domain.ports.analytics_repository import (
    AnalyticsRepository,
    FundMetadata,
    TickerPerformance,
)
from domain.ports.holding_repository import HoldingRepository


class TickerAnalytics(BaseModel):
    """Analytics for a single ticker/holding."""

    ticker: str
    name: str
    asset_class: str
    sector: str
    total_return_pct: float
    annualized_return_pct: float
    volatility_pct: float
    sharpe_ratio: float
    vs_benchmark_pct: float
    expense_ratio: float | None = None

    model_config = {"frozen": True}


class AssetClassBreakdown(BaseModel):
    """Breakdown by asset class."""

    asset_class: str
    count: int
    avg_return: float

    model_config = {"frozen": True}


class SectorBreakdown(BaseModel):
    """Breakdown by sector."""

    sector: str
    count: int
    avg_return: float

    model_config = {"frozen": True}


class PortfolioAnalytics(BaseModel):
    """Aggregated portfolio analytics."""

    holdings_count: int
    avg_total_return_pct: float
    avg_annualized_return_pct: float
    avg_sharpe_ratio: float
    beat_benchmark_count: int
    holdings: list[TickerAnalytics]
    asset_class_breakdown: list[AssetClassBreakdown]
    sector_breakdown: list[SectorBreakdown]

    model_config = {"frozen": True}


class ComputeAnalyticsCommand:
    """Command to compute portfolio analytics for a session."""

    def __init__(
        self,
        holding_repository: HoldingRepository,
        analytics_repository: AnalyticsRepository,
    ) -> None:
        self._holding_repository = holding_repository
        self._analytics_repository = analytics_repository

    def execute(self, session_id: UUID | None) -> PortfolioAnalytics:
        """Compute and return analytics for all holdings (session_id ignored for now)."""
        holdings = self._holding_repository.get_by_session_id(session_id)

        if not holdings:
            return PortfolioAnalytics(
                holdings_count=0,
                avg_total_return_pct=0.0,
                avg_annualized_return_pct=0.0,
                avg_sharpe_ratio=0.0,
                beat_benchmark_count=0,
                holdings=[],
                asset_class_breakdown=[],
                sector_breakdown=[],
            )

        tickers = list({h.ticker for h in holdings})

        performance_data = self._analytics_repository.get_performance_for_tickers(
            tickers
        )
        metadata = self._analytics_repository.get_fund_metadata_for_tickers(tickers)

        performance_by_ticker = self._index_performance_by_ticker(performance_data)
        metadata_by_ticker = self._index_metadata_by_ticker(metadata)

        ticker_analytics = self._build_ticker_analytics(
            holdings, performance_by_ticker, metadata_by_ticker
        )

        portfolio_metrics = self._compute_portfolio_metrics(ticker_analytics)
        asset_class_breakdown = self._compute_asset_class_breakdown(
            holdings, ticker_analytics
        )
        sector_breakdown = self._compute_sector_breakdown(holdings, ticker_analytics)

        return PortfolioAnalytics(
            holdings_count=len(holdings),
            avg_total_return_pct=portfolio_metrics["avg_total_return"],
            avg_annualized_return_pct=portfolio_metrics["avg_annualized_return"],
            avg_sharpe_ratio=portfolio_metrics["avg_sharpe"],
            beat_benchmark_count=portfolio_metrics["beat_benchmark_count"],
            holdings=ticker_analytics,
            asset_class_breakdown=asset_class_breakdown,
            sector_breakdown=sector_breakdown,
        )

    def _index_performance_by_ticker(
        self, performance_data: list[TickerPerformance]
    ) -> dict[str, TickerPerformance]:
        """Get the latest performance record for each ticker."""
        latest: dict[str, TickerPerformance] = {}
        for perf in performance_data:
            if perf.ticker not in latest or perf.date > latest[perf.ticker].date:
                latest[perf.ticker] = perf
        return latest

    def _index_metadata_by_ticker(
        self, metadata: list[FundMetadata]
    ) -> dict[str, FundMetadata]:
        """Index metadata by ticker."""
        return {m.ticker: m for m in metadata}

    def _build_ticker_analytics(
        self,
        holdings: list[Holding],
        performance_by_ticker: dict[str, TickerPerformance],
        metadata_by_ticker: dict[str, FundMetadata],
    ) -> list[TickerAnalytics]:
        """Build analytics for each ticker."""
        result: list[TickerAnalytics] = []

        for holding in holdings:
            perf = performance_by_ticker.get(holding.ticker)
            meta = metadata_by_ticker.get(holding.ticker)

            # Convert Decimal to float and provide defaults
            total_return = float(perf.cumulative_return) if perf and perf.cumulative_return else 0.0
            volatility = float(perf.volatility) if perf and perf.volatility else 0.0
            expense_ratio = float(meta.expense_ratio) if meta and meta.expense_ratio else None

            # TODO: Calculate actual metrics from DuckDB data
            # For now, using placeholder values
            analytics = TickerAnalytics(
                ticker=holding.ticker,
                name=holding.name,
                asset_class=holding.asset_class,
                sector=holding.sector,
                total_return_pct=total_return * 100,
                annualized_return_pct=total_return * 100,  # Simplified
                volatility_pct=volatility * 100,
                sharpe_ratio=0.0,  # TODO: Calculate Sharpe ratio
                vs_benchmark_pct=0.0,  # TODO: Calculate vs benchmark
                expense_ratio=expense_ratio,
            )
            result.append(analytics)

        return result

    def _compute_portfolio_metrics(
        self, ticker_analytics: list[TickerAnalytics]
    ) -> dict[str, float]:
        """Compute portfolio-level aggregate metrics."""
        if not ticker_analytics:
            return {
                "avg_total_return": 0.0,
                "avg_annualized_return": 0.0,
                "avg_sharpe": 0.0,
                "beat_benchmark_count": 0,
            }

        total_returns = [t.total_return_pct for t in ticker_analytics]
        annualized_returns = [t.annualized_return_pct for t in ticker_analytics]
        sharpe_ratios = [t.sharpe_ratio for t in ticker_analytics]
        beat_benchmark = sum(1 for t in ticker_analytics if t.vs_benchmark_pct > 0)

        return {
            "avg_total_return": sum(total_returns) / len(total_returns),
            "avg_annualized_return": sum(annualized_returns) / len(annualized_returns),
            "avg_sharpe": sum(sharpe_ratios) / len(sharpe_ratios),
            "beat_benchmark_count": beat_benchmark,
        }

    def _compute_asset_class_breakdown(
        self, holdings: list[Holding], ticker_analytics: list[TickerAnalytics]
    ) -> list[AssetClassBreakdown]:
        """Compute breakdown by asset class with average returns."""
        analytics_by_ticker = {t.ticker: t for t in ticker_analytics}
        breakdown: dict[str, list[float]] = {}

        for holding in holdings:
            analytics = analytics_by_ticker.get(holding.ticker)
            if analytics:
                if holding.asset_class not in breakdown:
                    breakdown[holding.asset_class] = []
                breakdown[holding.asset_class].append(analytics.total_return_pct)

        return [
            AssetClassBreakdown(
                asset_class=asset_class,
                count=len(returns),
                avg_return=sum(returns) / len(returns) if returns else 0.0,
            )
            for asset_class, returns in breakdown.items()
        ]

    def _compute_sector_breakdown(
        self, holdings: list[Holding], ticker_analytics: list[TickerAnalytics]
    ) -> list[SectorBreakdown]:
        """Compute breakdown by sector with average returns."""
        analytics_by_ticker = {t.ticker: t for t in ticker_analytics}
        breakdown: dict[str, list[float]] = {}

        for holding in holdings:
            analytics = analytics_by_ticker.get(holding.ticker)
            if analytics:
                if holding.sector not in breakdown:
                    breakdown[holding.sector] = []
                breakdown[holding.sector].append(analytics.total_return_pct)

        return [
            SectorBreakdown(
                sector=sector,
                count=len(returns),
                avg_return=sum(returns) / len(returns) if returns else 0.0,
            )
            for sector, returns in breakdown.items()
        ]
