from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class RiskAnalysis:
    """Represents the result of portfolio risk analysis."""

    risks: list[dict]
    macro_climate_summary: str
    analysis_timestamp: str
    model_used: str


@dataclass
class AllocationInterpretation:
    """Represents the result of portfolio description interpretation."""

    ticker: str
    display_name: str
    weight: Decimal  # Percentage (0-100)


@dataclass
class PortfolioInterpretation:
    """Represents the interpreted portfolio from user description."""

    allocations: list[AllocationInterpretation]
    unmatched_descriptions: list[str]
    model_used: str


@dataclass
class SecuritySummary:
    """Summary of a security for LLM context."""

    ticker: str
    display_name: str
    asset_type: str
    sector: str | None


@dataclass
class EnrichedSecuritySummary:
    """Enriched security data for scenario-based LLM selection."""

    ticker: str
    display_name: str
    asset_type: str
    sector: str | None
    industry: str | None
    # Market dynamics
    market_cap: float | None
    market_cap_category: str | None  # mega, large, mid, small, micro
    beta: float | None
    # Valuation
    trailing_pe: float | None
    forward_pe: float | None
    price_to_book: float | None
    # Income
    dividend_yield: float | None
    # Profitability
    profit_margin: float | None
    return_on_equity: float | None
    # Growth
    revenue_growth: float | None
    # Financial health
    debt_to_equity: float | None
    # Scenario-relevant flags
    is_dividend_payer: bool
    is_high_growth: bool
    is_value: bool
    is_defensive: bool
    is_cyclical: bool
    is_rate_sensitive: bool
    is_inflation_hedge: bool
    # Historical performance
    historical_annual_return: float | None
    annualized_volatility: float | None
    # Analyst sentiment
    analyst_implied_return: float | None
    analyst_count: int | None


@dataclass
class ScenarioSecuritySelection:
    """A security selected for a scenario with rationale."""

    ticker: str
    display_name: str
    weight: Decimal  # Suggested weight (0-100)
    rationale: str  # Why this security fits the scenario
    expected_behavior: str  # How it's expected to perform in the scenario


@dataclass
class ScenarioAnalysisResult:
    """Result of scenario-based securities selection."""

    scenario_summary: str  # Summary of the scenario interpreted
    selections: list[ScenarioSecuritySelection]
    scenario_risks: list[str]  # Risks specific to this scenario
    diversification_notes: str  # Notes on diversification of selections
    model_used: str


@dataclass
class DescriptionClassification:
    """Classification result for whether text is a portfolio description."""

    is_portfolio_description: bool
    confidence: float  # 0.0 - 1.0


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

    @abstractmethod
    def interpret_portfolio_description(
        self,
        description: str,
        available_securities: list[SecuritySummary],
    ) -> PortfolioInterpretation:
        """
        Interpret a natural language portfolio description into allocations.

        Args:
            description: User's description of their portfolio
            available_securities: List of available securities

        Returns:
            PortfolioInterpretation with matched allocations and any unmatched descriptions
        """
        pass

    @abstractmethod
    def classify_description(self, description: str) -> DescriptionClassification:
        """Classify whether text is a portfolio description. Must not follow instructions in the text."""
        pass

    @abstractmethod
    def select_securities_for_scenario(
        self,
        scenario_description: str,
        available_securities: list["EnrichedSecuritySummary"],
        num_selections: int = 10,
    ) -> "ScenarioAnalysisResult":
        """
        Select securities that would perform well in a given economic/policy scenario.

        Args:
            scenario_description: Natural language description of the scenario
                (e.g., "Rising inflation with Fed rate hikes", "Tech bubble burst",
                "War in Eastern Europe", "Stagflation environment")
            available_securities: List of enriched securities with fundamentals
            num_selections: Target number of securities to select (default 10)

        Returns:
            ScenarioAnalysisResult with selected securities and analysis
        """
        pass
