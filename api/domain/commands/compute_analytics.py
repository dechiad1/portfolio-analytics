from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from domain.models.position import Position
from domain.ports.analytics_repository import (
    AnalyticsRepository,
    FundMetadata,
    TickerPerformance,
)
from domain.ports.position_repository import PositionRepository


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
        position_repository: PositionRepository,
        analytics_repository: AnalyticsRepository,
    ) -> None:
        self._position_repository = position_repository
        self._analytics_repository = analytics_repository

    def execute(self, portfolio_id: UUID | None = None) -> PortfolioAnalytics:
        """Compute and return analytics for all positions."""
        positions = self._position_repository.get_all()

        if not positions:
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

        tickers = list({p.ticker for p in positions if p.ticker})

        performance_data = self._analytics_repository.get_performance_for_tickers(
            tickers
        )
        metadata = self._analytics_repository.get_fund_metadata_for_tickers(tickers)

        performance_by_ticker = self._index_performance_by_ticker(performance_data)
        metadata_by_ticker = self._index_metadata_by_ticker(metadata)

        ticker_analytics = self._build_ticker_analytics(
            positions, performance_by_ticker, metadata_by_ticker
        )

        portfolio_metrics = self._compute_portfolio_metrics(ticker_analytics)
        asset_class_breakdown = self._compute_asset_class_breakdown(
            positions, ticker_analytics
        )
        sector_breakdown = self._compute_sector_breakdown(positions, ticker_analytics)

        return PortfolioAnalytics(
            holdings_count=len(positions),
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
        """Index performance records by ticker."""
        return {perf.ticker: perf for perf in performance_data}

    def _index_metadata_by_ticker(
        self, metadata: list[FundMetadata]
    ) -> dict[str, FundMetadata]:
        """Index metadata by ticker."""
        return {m.ticker: m for m in metadata}

    def _build_ticker_analytics(
        self,
        positions: list[Position],
        performance_by_ticker: dict[str, TickerPerformance],
        metadata_by_ticker: dict[str, FundMetadata],
    ) -> list[TickerAnalytics]:
        """Build analytics for each ticker."""
        result: list[TickerAnalytics] = []

        for position in positions:
            ticker = position.ticker
            if not ticker:
                continue

            perf = performance_by_ticker.get(ticker)
            meta = metadata_by_ticker.get(ticker)

            # Convert Decimal to float and provide defaults
            total_return = float(perf.total_return_pct) if perf and perf.total_return_pct else 0.0
            annualized_return = float(perf.annualized_return_pct) if perf and perf.annualized_return_pct else 0.0
            volatility = float(perf.volatility_pct) if perf and perf.volatility_pct else 0.0
            sharpe = float(perf.sharpe_ratio) if perf and perf.sharpe_ratio else 0.0
            vs_benchmark = float(perf.vs_benchmark_pct) if perf and perf.vs_benchmark_pct else 0.0
            expense_ratio = float(meta.expense_ratio) if meta and meta.expense_ratio else None

            # Get name and other attributes from security if available
            name = position.security.display_name if position.security else ticker
            asset_class = "Unknown"  # Not tracked in positions
            sector = position.security.sector if position.security else "Unknown"

            analytics = TickerAnalytics(
                ticker=ticker,
                name=name,
                asset_class=asset_class,
                sector=sector,
                total_return_pct=total_return,
                annualized_return_pct=annualized_return,
                volatility_pct=volatility,
                sharpe_ratio=sharpe,
                vs_benchmark_pct=vs_benchmark,
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
        self, positions: list[Position], ticker_analytics: list[TickerAnalytics]
    ) -> list[AssetClassBreakdown]:
        """Compute breakdown by asset class with average returns."""
        analytics_by_ticker = {t.ticker: t for t in ticker_analytics}
        breakdown: dict[str, list[float]] = {}

        for position in positions:
            ticker = position.ticker
            if not ticker:
                continue
            analytics = analytics_by_ticker.get(ticker)
            if analytics:
                asset_class = analytics.asset_class
                if asset_class not in breakdown:
                    breakdown[asset_class] = []
                breakdown[asset_class].append(analytics.total_return_pct)

        return [
            AssetClassBreakdown(
                asset_class=asset_class,
                count=len(returns),
                avg_return=sum(returns) / len(returns) if returns else 0.0,
            )
            for asset_class, returns in breakdown.items()
        ]

    def _compute_sector_breakdown(
        self, positions: list[Position], ticker_analytics: list[TickerAnalytics]
    ) -> list[SectorBreakdown]:
        """Compute breakdown by sector with average returns."""
        analytics_by_ticker = {t.ticker: t for t in ticker_analytics}
        breakdown: dict[str, list[float]] = {}

        for position in positions:
            ticker = position.ticker
            if not ticker:
                continue
            analytics = analytics_by_ticker.get(ticker)
            if analytics:
                sector = analytics.sector
                if sector not in breakdown:
                    breakdown[sector] = []
                breakdown[sector].append(analytics.total_return_pct)

        return [
            SectorBreakdown(
                sector=sector,
                count=len(returns),
                avg_return=sum(returns) / len(returns) if returns else 0.0,
            )
            for sector, returns in breakdown.items()
        ]
