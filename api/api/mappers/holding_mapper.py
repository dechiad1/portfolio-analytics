from domain.models.holding import Holding
from domain.commands.compute_analytics import HoldingAnalytics, PortfolioAnalytics
from api.schemas.holding import HoldingResponse, HoldingListResponse, BulkCreateHoldingsResponse
from api.schemas.analytics import HoldingAnalyticsResponse, AnalyticsResponse


class HoldingMapper:
    """Maps between Holding domain models and API schemas."""

    @staticmethod
    def to_response(holding: Holding) -> HoldingResponse:
        """Convert a Holding domain model to a HoldingResponse."""
        return HoldingResponse(
            id=holding.id,
            session_id=holding.session_id,
            ticker=holding.ticker,
            name=holding.name,
            asset_class=holding.asset_class,
            sector=holding.sector,
            broker=holding.broker,
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
            session_id=analytics.session_id,
            total_holdings=analytics.total_holdings,
            holdings=[
                HoldingMapper._holding_analytics_to_response(h)
                for h in analytics.holdings
            ],
            portfolio_avg_return=analytics.portfolio_avg_return,
            portfolio_avg_volatility=analytics.portfolio_avg_volatility,
            asset_class_breakdown=analytics.asset_class_breakdown,
            sector_breakdown=analytics.sector_breakdown,
            broker_breakdown=analytics.broker_breakdown,
        )

    @staticmethod
    def _holding_analytics_to_response(
        holding: HoldingAnalytics,
    ) -> HoldingAnalyticsResponse:
        """Convert HoldingAnalytics to HoldingAnalyticsResponse."""
        return HoldingAnalyticsResponse(
            ticker=holding.ticker,
            name=holding.name,
            asset_class=holding.asset_class,
            sector=holding.sector,
            broker=holding.broker,
            purchase_date=holding.purchase_date,
            latest_return=holding.latest_return,
            cumulative_return=holding.cumulative_return,
            volatility=holding.volatility,
            expense_ratio=holding.expense_ratio,
            category=holding.category,
        )
