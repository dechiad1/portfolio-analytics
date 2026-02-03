"""Mapper for analytics domain objects to API responses."""

from domain.commands.compute_analytics import PortfolioAnalytics
from api.schemas.analytics import (
    AnalyticsResponse,
    TickerAnalyticsResponse,
    AssetClassBreakdownResponse,
    SectorBreakdownResponse,
)


class AnalyticsMapper:
    """Maps analytics domain objects to API response schemas."""

    @staticmethod
    def analytics_to_response(analytics: PortfolioAnalytics) -> AnalyticsResponse:
        """Convert PortfolioAnalytics to AnalyticsResponse."""
        return AnalyticsResponse(
            holdings_count=analytics.holdings_count,
            avg_total_return_pct=analytics.avg_total_return_pct,
            avg_annualized_return_pct=analytics.avg_annualized_return_pct,
            avg_sharpe_ratio=analytics.avg_sharpe_ratio,
            beat_benchmark_count=analytics.beat_benchmark_count,
            holdings=[
                TickerAnalyticsResponse(
                    ticker=h.ticker,
                    name=h.name,
                    asset_class=h.asset_class,
                    sector=h.sector,
                    total_return_pct=h.total_return_pct,
                    annualized_return_pct=h.annualized_return_pct,
                    volatility_pct=h.volatility_pct,
                    sharpe_ratio=h.sharpe_ratio,
                    vs_benchmark_pct=h.vs_benchmark_pct,
                    expense_ratio=h.expense_ratio,
                )
                for h in analytics.holdings
            ],
            asset_class_breakdown=[
                AssetClassBreakdownResponse(
                    asset_class=b.asset_class,
                    count=b.count,
                    avg_return=b.avg_return,
                )
                for b in analytics.asset_class_breakdown
            ],
            sector_breakdown=[
                SectorBreakdownResponse(
                    sector=b.sector,
                    count=b.count,
                    avg_return=b.avg_return,
                )
                for b in analytics.sector_breakdown
            ],
        )
