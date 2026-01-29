from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.risk_analysis import RiskAnalysis


class RiskAnalysisRepository(ABC):
    """Port for risk analysis persistence operations."""

    @abstractmethod
    def create(self, analysis: RiskAnalysis) -> RiskAnalysis:
        """Persist a new risk analysis."""
        pass

    @abstractmethod
    def get_by_id(self, id: UUID) -> RiskAnalysis | None:
        """Retrieve a risk analysis by ID."""
        pass

    @abstractmethod
    def get_by_portfolio_id(self, portfolio_id: UUID) -> list[RiskAnalysis]:
        """Retrieve all risk analyses for a portfolio, ordered by created_at desc."""
        pass

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        """Delete a risk analysis by ID. Returns True if deleted."""
        pass

    @abstractmethod
    def get_portfolio_id_for_analysis(self, id: UUID) -> UUID | None:
        """Get the portfolio_id for a risk analysis (for ownership checks)."""
        pass
