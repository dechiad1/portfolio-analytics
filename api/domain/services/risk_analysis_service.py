from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.models.position import Position
from domain.models.risk_analysis import RiskAnalysis
from domain.ports.llm_repository import LLMRepository
from domain.ports.llm_repository import RiskAnalysis as LLMRiskAnalysis
from domain.ports.portfolio_repository import PortfolioRepository
from domain.ports.position_repository import PositionRepository
from domain.ports.risk_analysis_repository import RiskAnalysisRepository
from domain.services.portfolio_service import (
    PortfolioNotFoundError,
    PortfolioAccessDeniedError,
)

LLM_UNAVAILABLE_MESSAGE = "LLM analysis unavailable. API key not configured."


class RiskAnalysisNotFoundError(Exception):
    """Raised when a risk analysis is not found."""

    pass


class RiskAnalysisAccessDeniedError(Exception):
    """Raised when access to a risk analysis is denied."""

    pass


class RiskAnalysisService:
    """Service for portfolio risk analysis using LLM."""

    def __init__(
        self,
        llm_repository: LLMRepository | None,
        portfolio_repository: PortfolioRepository,
        position_repository: PositionRepository,
        risk_analysis_repository: RiskAnalysisRepository | None = None,
    ) -> None:
        self._llm_repo = llm_repository
        self._portfolio_repo = portfolio_repository
        self._position_repo = position_repository
        self._risk_analysis_repo = risk_analysis_repository

    def analyze_portfolio_risks(
        self,
        portfolio_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
    ) -> RiskAnalysis:
        """Analyze risks for a portfolio using LLM with macro context.

        Persists the result if a repository is configured.
        """
        # Get portfolio
        portfolio = self._portfolio_repo.get_by_id(portfolio_id)
        if portfolio is None:
            raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")
        if not is_admin and portfolio.user_id != user_id:
            raise PortfolioAccessDeniedError("Access denied to this portfolio")

        # Get positions
        positions = self._position_repo.get_by_portfolio_id(portfolio_id)
        summary = self._calculate_summary(portfolio, positions)
        holdings_data = self._positions_to_dict(positions, summary["total_value"])

        # Get LLM analysis
        if self._llm_repo is None:
            llm_result = LLMRiskAnalysis(
                risks=[],
                macro_climate_summary=LLM_UNAVAILABLE_MESSAGE,
                analysis_timestamp=datetime.now(timezone.utc).isoformat(),
                model_used="unavailable",
            )
        else:
            llm_result = self._llm_repo.analyze_portfolio_risks(summary, holdings_data)

        # Create domain model
        analysis = RiskAnalysis(
            id=uuid4(),
            portfolio_id=portfolio_id,
            risks=llm_result.risks,
            macro_climate_summary=llm_result.macro_climate_summary,
            model_used=llm_result.model_used,
            created_at=datetime.now(timezone.utc),
        )

        # Persist if repository is available
        if self._risk_analysis_repo is not None:
            analysis = self._risk_analysis_repo.create(analysis)

        return analysis

    def get_analysis(
        self,
        analysis_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
    ) -> RiskAnalysis:
        """Get a specific risk analysis by ID."""
        if self._risk_analysis_repo is None:
            raise RiskAnalysisNotFoundError(f"Risk analysis {analysis_id} not found")

        analysis = self._risk_analysis_repo.get_by_id(analysis_id)
        if analysis is None:
            raise RiskAnalysisNotFoundError(f"Risk analysis {analysis_id} not found")

        # Verify access
        portfolio = self._portfolio_repo.get_by_id(analysis.portfolio_id)
        if portfolio is None:
            raise RiskAnalysisNotFoundError(f"Risk analysis {analysis_id} not found")
        if not is_admin and portfolio.user_id != user_id:
            raise RiskAnalysisAccessDeniedError("Access denied to this risk analysis")

        return analysis

    def list_analyses(
        self,
        portfolio_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
    ) -> list[RiskAnalysis]:
        """List all risk analyses for a portfolio, ordered by created_at desc."""
        # Verify portfolio access
        portfolio = self._portfolio_repo.get_by_id(portfolio_id)
        if portfolio is None:
            raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")
        if not is_admin and portfolio.user_id != user_id:
            raise PortfolioAccessDeniedError("Access denied to this portfolio")

        if self._risk_analysis_repo is None:
            return []

        return self._risk_analysis_repo.get_by_portfolio_id(portfolio_id)

    def delete_analysis(
        self,
        analysis_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
    ) -> bool:
        """Delete a risk analysis by ID. Returns True if deleted."""
        if self._risk_analysis_repo is None:
            raise RiskAnalysisNotFoundError(f"Risk analysis {analysis_id} not found")

        # Verify access via portfolio ownership
        portfolio_id = self._risk_analysis_repo.get_portfolio_id_for_analysis(analysis_id)
        if portfolio_id is None:
            raise RiskAnalysisNotFoundError(f"Risk analysis {analysis_id} not found")

        portfolio = self._portfolio_repo.get_by_id(portfolio_id)
        if portfolio is None:
            raise RiskAnalysisNotFoundError(f"Risk analysis {analysis_id} not found")
        if not is_admin and portfolio.user_id != user_id:
            raise RiskAnalysisAccessDeniedError("Access denied to this risk analysis")

        return self._risk_analysis_repo.delete(analysis_id)

    def _calculate_summary(self, portfolio, positions: list[Position]) -> dict:
        """Calculate portfolio summary statistics from positions."""
        from decimal import Decimal

        total_value = Decimal("0")
        total_cost = Decimal("0")
        by_asset_type: dict[str, Decimal] = {}
        by_sector: dict[str, Decimal] = {}

        for p in positions:
            # Use market_value if available, else cost_basis
            value = p.market_value if p.market_value else p.cost_basis
            total_value += value
            total_cost += p.cost_basis

            if p.security:
                asset_type = p.security.asset_type or "Unknown"
                sector = p.security.sector or "Unknown"
                by_asset_type[asset_type] = by_asset_type.get(asset_type, Decimal("0")) + value
                by_sector[sector] = by_sector.get(sector, Decimal("0")) + value

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
            "holdings_count": len(positions),
            "by_asset_type": to_percentages(by_asset_type),
            "by_asset_class": [],  # Not tracked in positions
            "by_sector": to_percentages(by_sector),
        }

    def _positions_to_dict(
        self, positions: list[Position], total_value: float
    ) -> list[dict]:
        """Convert positions to dict format with weight calculation."""
        result = []
        for p in positions:
            value = float(p.market_value) if p.market_value else float(p.cost_basis)
            weight = (value / total_value * 100) if total_value > 0 else 0
            result.append({
                "ticker": p.ticker or "UNKNOWN",
                "name": p.security.display_name if p.security else "Unknown",
                "asset_type": p.security.asset_type if p.security else "equity",
                "asset_class": "Unknown",  # Not tracked in positions
                "sector": p.security.sector if p.security else "Unknown",
                "market_value": value,
                "weight": weight,
            })
        return result
