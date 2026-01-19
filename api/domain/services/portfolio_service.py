from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from domain.models.portfolio import Portfolio
from domain.models.holding import Holding
from domain.ports.portfolio_repository import PortfolioRepository
from domain.ports.holding_repository import HoldingRepository


class PortfolioNotFoundError(Exception):
    """Raised when a portfolio is not found."""
    pass


class PortfolioAccessDeniedError(Exception):
    """Raised when user doesn't have access to a portfolio."""
    pass


class PortfolioService:
    """Service for managing user portfolios."""

    def __init__(
        self,
        portfolio_repository: PortfolioRepository,
        holding_repository: HoldingRepository,
    ) -> None:
        self._portfolio_repo = portfolio_repository
        self._holding_repo = holding_repository

    def create_portfolio(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> Portfolio:
        """Create a new portfolio for a user."""
        now = datetime.now(timezone.utc)
        portfolio = Portfolio(
            id=uuid4(),
            user_id=user_id,
            name=name.strip(),
            description=description.strip() if description else None,
            created_at=now,
            updated_at=now,
        )
        return self._portfolio_repo.create(portfolio)

    def get_portfolio(self, portfolio_id: UUID, user_id: UUID) -> Portfolio:
        """Get a portfolio by ID, verifying ownership."""
        portfolio = self._portfolio_repo.get_by_id(portfolio_id)
        if portfolio is None:
            raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")
        if portfolio.user_id != user_id:
            raise PortfolioAccessDeniedError("Access denied to this portfolio")
        return portfolio

    def get_user_portfolios(self, user_id: UUID) -> list[Portfolio]:
        """Get all portfolios for a user."""
        return self._portfolio_repo.get_by_user_id(user_id)

    def update_portfolio(
        self,
        portfolio_id: UUID,
        user_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Portfolio:
        """Update a portfolio."""
        existing = self.get_portfolio(portfolio_id, user_id)

        updated = Portfolio(
            id=existing.id,
            user_id=existing.user_id,
            name=name.strip() if name else existing.name,
            description=description.strip() if description is not None else existing.description,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        return self._portfolio_repo.update(updated)

    def delete_portfolio(self, portfolio_id: UUID, user_id: UUID) -> None:
        """Delete a portfolio and all its holdings."""
        self.get_portfolio(portfolio_id, user_id)  # Verify access
        self._portfolio_repo.delete(portfolio_id)

    def get_portfolio_holdings(self, portfolio_id: UUID, user_id: UUID) -> list[Holding]:
        """Get all holdings in a portfolio."""
        self.get_portfolio(portfolio_id, user_id)  # Verify access
        return self._holding_repo.get_by_portfolio_id(portfolio_id)

    def get_portfolio_summary(self, portfolio_id: UUID, user_id: UUID) -> dict:
        """Get a summary of portfolio composition and value."""
        portfolio = self.get_portfolio(portfolio_id, user_id)
        holdings = self._holding_repo.get_by_portfolio_id(portfolio_id)

        total_value = Decimal("0")
        total_cost = Decimal("0")
        by_asset_type: dict[str, Decimal] = {}
        by_asset_class: dict[str, Decimal] = {}
        by_sector: dict[str, Decimal] = {}

        for h in holdings:
            value = h.market_value
            total_value += value
            total_cost += h.cost_basis

            by_asset_type[h.asset_type] = by_asset_type.get(h.asset_type, Decimal("0")) + value
            by_asset_class[h.asset_class] = by_asset_class.get(h.asset_class, Decimal("0")) + value
            by_sector[h.sector] = by_sector.get(h.sector, Decimal("0")) + value

        def to_percentages(breakdown: dict[str, Decimal]) -> list[dict]:
            if total_value == 0:
                return []
            return [
                {
                    "name": name,
                    "value": float(value),
                    "percentage": float((value / total_value) * 100),
                }
                for name, value in sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
            ]

        return {
            "portfolio_id": str(portfolio.id),
            "portfolio_name": portfolio.name,
            "total_value": float(total_value),
            "total_cost": float(total_cost),
            "total_gain_loss": float(total_value - total_cost),
            "total_gain_loss_percent": float(((total_value - total_cost) / total_cost * 100)) if total_cost > 0 else 0,
            "holdings_count": len(holdings),
            "by_asset_type": to_percentages(by_asset_type),
            "by_asset_class": to_percentages(by_asset_class),
            "by_sector": to_percentages(by_sector),
        }
