from domain.models.portfolio import Portfolio
from api.schemas.portfolio import (
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioSummaryResponse,
    PortfolioWithUserResponse,
    AllPortfoliosListResponse,
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
            base_currency=portfolio.base_currency,
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

    @staticmethod
    def to_with_user_response(
        portfolio: Portfolio, user_email: str
    ) -> PortfolioWithUserResponse:
        """Map Portfolio with user email to PortfolioWithUserResponse."""
        return PortfolioWithUserResponse(
            id=portfolio.id,
            user_id=portfolio.user_id,
            user_email=user_email,
            name=portfolio.name,
            base_currency=portfolio.base_currency,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
        )

    @staticmethod
    def to_all_portfolios_response(
        portfolios_with_users: list[tuple[Portfolio, str]]
    ) -> AllPortfoliosListResponse:
        """Map list of (Portfolio, email) to AllPortfoliosListResponse."""
        return AllPortfoliosListResponse(
            portfolios=[
                PortfolioMapper.to_with_user_response(p, email)
                for p, email in portfolios_with_users
            ],
            count=len(portfolios_with_users),
        )
