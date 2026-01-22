from domain.models.portfolio import Portfolio
from api.schemas.portfolio import (
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioSummaryResponse,
    AssetBreakdown,
)


class PortfolioMapper:
    """Mapper for portfolio-related data transformations."""

    @staticmethod
    def to_response(portfolio: Portfolio) -> PortfolioResponse:
        """Map Portfolio to PortfolioResponse."""
        return PortfolioResponse(
            id=portfolio.id,
            user_id=portfolio.user_id,
            name=portfolio.name,
            description=portfolio.description,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
        )

    @staticmethod
    def to_list_response(portfolios: list[Portfolio]) -> PortfolioListResponse:
        """Map list of Portfolio to PortfolioListResponse."""
        return PortfolioListResponse(
            portfolios=[PortfolioMapper.to_response(p) for p in portfolios],
            count=len(portfolios),
        )

    @staticmethod
    def to_summary_response(summary: dict) -> PortfolioSummaryResponse:
        """Map summary dict to PortfolioSummaryResponse."""
        return PortfolioSummaryResponse(
            portfolio_id=summary["portfolio_id"],
            portfolio_name=summary["portfolio_name"],
            total_value=summary["total_value"],
            total_cost=summary["total_cost"],
            total_gain_loss=summary["total_gain_loss"],
            total_gain_loss_percent=summary["total_gain_loss_percent"],
            holdings_count=summary["holdings_count"],
            by_asset_type=[
                AssetBreakdown(**item) for item in summary["by_asset_type"]
            ],
            by_asset_class=[
                AssetBreakdown(**item) for item in summary["by_asset_class"]
            ],
            by_sector=[
                AssetBreakdown(**item) for item in summary["by_sector"]
            ],
        )
