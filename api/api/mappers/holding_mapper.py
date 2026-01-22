from domain.models.holding import Holding
from domain.commands.compute_analytics import (
    TickerAnalytics,
    PortfolioAnalytics,
    AssetClassBreakdown,
    SectorBreakdown,
)
from api.schemas.holding import HoldingResponse, HoldingListResponse, BulkCreateHoldingsResponse
from api.schemas.analytics import (
    TickerAnalyticsResponse,
    AnalyticsResponse,
    AssetClassBreakdownResponse,
    SectorBreakdownResponse,
)


class HoldingMapper:
    """Maps between Holding domain models and API schemas."""

    @staticmethod
    def to_response(holding: Holding) -> HoldingResponse:
        """Convert a Holding domain model to a HoldingResponse."""
        return HoldingResponse(
            id=holding.id,
            portfolio_id=holding.portfolio_id,
            ticker=holding.ticker,
            name=holding.name,
            asset_type=holding.asset_type,
            asset_class=holding.asset_class,
            sector=holding.sector,
            broker=holding.broker,
            quantity=float(holding.quantity),
            purchase_price=float(holding.purchase_price),
            current_price=float(holding.current_price) if holding.current_price else None,
            market_value=float(holding.market_value),
            cost_basis=float(holding.cost_basis),
            gain_loss=float(holding.gain_loss),
            purchase_date=holding.purchase_date,
            created_at=holding.created_at,
        )

    @staticmethod
    def to_list_response(holdings: list[Holding]) -> HoldingListResponse:
        """Convert a list of Holding domain models to a HoldingListResponse."""
        return HoldingListResponse(
            holdings=[HoldingMapper.to_response(h) for h in holdings],
            count=len(holdings),
        )

    @staticmethod
    def to_bulk_create_response(holdings: list[Holding]) -> BulkCreateHoldingsResponse:
        """Convert created holdings to a BulkCreateHoldingsResponse."""
        return BulkCreateHoldingsResponse(
            created_count=len(holdings),
            holdings=[HoldingMapper.to_response(h) for h in holdings],
        )

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
                HoldingMapper._ticker_analytics_to_response(h)
                for h in analytics.holdings
            ],
            asset_class_breakdown=[
                HoldingMapper._asset_class_breakdown_to_response(b)
                for b in analytics.asset_class_breakdown
            ],
            sector_breakdown=[
                HoldingMapper._sector_breakdown_to_response(b)
                for b in analytics.sector_breakdown
            ],
        )

    @staticmethod
    def _ticker_analytics_to_response(
        ticker: TickerAnalytics,
    ) -> TickerAnalyticsResponse:
        """Convert TickerAnalytics to TickerAnalyticsResponse."""
        return TickerAnalyticsResponse(
            ticker=ticker.ticker,
            name=ticker.name,
            asset_class=ticker.asset_class,
            sector=ticker.sector,
            total_return_pct=ticker.total_return_pct,
            annualized_return_pct=ticker.annualized_return_pct,
            volatility_pct=ticker.volatility_pct,
            sharpe_ratio=ticker.sharpe_ratio,
            vs_benchmark_pct=ticker.vs_benchmark_pct,
            expense_ratio=ticker.expense_ratio,
        )

    @staticmethod
    def _asset_class_breakdown_to_response(
        breakdown: AssetClassBreakdown,
    ) -> AssetClassBreakdownResponse:
        """Convert AssetClassBreakdown to AssetClassBreakdownResponse."""
        return AssetClassBreakdownResponse(
            asset_class=breakdown.asset_class,
            count=breakdown.count,
            avg_return=breakdown.avg_return,
        )

    @staticmethod
    def _sector_breakdown_to_response(
        breakdown: SectorBreakdown,
    ) -> SectorBreakdownResponse:
        """Convert SectorBreakdown to SectorBreakdownResponse."""
        return SectorBreakdownResponse(
            sector=breakdown.sector,
            count=breakdown.count,
            avg_return=breakdown.avg_return,
        )
