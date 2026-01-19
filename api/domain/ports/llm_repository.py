from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RiskAnalysis:
    """Represents the result of portfolio risk analysis."""

    risks: list[dict]
    macro_climate_summary: str
    analysis_timestamp: str
    model_used: str


class LLMRepository(ABC):
    """Port for LLM-based analysis operations."""

    @abstractmethod
    def analyze_portfolio_risks(
        self,
        portfolio_summary: dict,
        holdings: list[dict],
    ) -> RiskAnalysis:
        """Analyze portfolio risks using LLM with web search for macro context."""
        pass
