from uuid import UUID

from domain.models.holding import Holding
from domain.ports.llm_repository import LLMRepository, RiskAnalysis
from domain.ports.portfolio_repository import PortfolioRepository
from domain.ports.holding_repository import HoldingRepository


class RiskAnalysisService:
    """Service for portfolio risk analysis using LLM."""

    def __init__(
        self,
        llm_repository: LLMRepository,
        portfolio_repository: PortfolioRepository,
        holding_repository: HoldingRepository,
    ) -> None:
        self._llm_repo = llm_repository
        self._portfolio_repo = portfolio_repository
        self._holding_repo = holding_repository

    def analyze_portfolio_risks(
        self,
        portfolio_id: UUID,
        user_id: UUID,
    ) -> RiskAnalysis:
        """Analyze risks for a portfolio using LLM with macro context."""
        # Get portfolio
        portfolio = self._portfolio_repo.get_by_id(portfolio_id)
        if portfolio is None:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        if portfolio.user_id != user_id:
            raise ValueError("Access denied to this portfolio")

        # Get holdings
        holdings = self._holding_repo.get_by_portfolio_id(portfolio_id)

        # Calculate portfolio summary
        summary = self._calculate_summary(portfolio, holdings)

        # Convert holdings to dict format for LLM
        holdings_data = self._holdings_to_dict(holdings, summary["total_value"])

        # Get LLM analysis
        return self._llm_repo.analyze_portfolio_risks(summary, holdings_data)

    def _calculate_summary(self, portfolio, holdings: list[Holding]) -> dict:
        """Calculate portfolio summary statistics."""
        from decimal import Decimal

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

    def _holdings_to_dict(self, holdings: list[Holding], total_value: float) -> list[dict]:
        """Convert holdings to dict format with weight calculation."""
        result = []
        for h in holdings:
            market_value = float(h.market_value)
            weight = (market_value / total_value * 100) if total_value > 0 else 0
            result.append({
                "ticker": h.ticker,
                "name": h.name,
                "asset_type": h.asset_type,
                "asset_class": h.asset_class,
                "sector": h.sector,
                "market_value": market_value,
                "weight": weight,
            })
        return result
