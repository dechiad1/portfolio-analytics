"""Service for LLM-based scenario securities selection."""

import re
from dataclasses import dataclass
from decimal import Decimal

from domain.ports.analytics_repository import AnalyticsRepository
from domain.ports.llm_repository import (
    LLMRepository,
    EnrichedSecuritySummary,
    ScenarioAnalysisResult,
)
from domain.value_objects import EnrichedSecurity


@dataclass
class ScenarioSelectionResponse:
    """Response from scenario-based securities selection."""

    scenario_summary: str
    selections: list["SelectedSecurity"]
    scenario_risks: list[str]
    diversification_notes: str
    model_used: str
    securities_analyzed: int


@dataclass
class SelectedSecurity:
    """A security selected for the scenario."""

    ticker: str
    display_name: str
    weight: Decimal  # Percentage (0-100)
    rationale: str
    expected_behavior: str
    # Enriched data for context
    sector: str | None
    market_cap_category: str | None
    beta: float | None
    dividend_yield: float | None


class ScenarioSelectionService:
    """
    Service for selecting securities based on economic/policy scenarios.

    Uses LLM to analyze scenarios and select securities from the enriched
    securities data that would likely perform well if the scenario materializes.
    """

    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
        llm_repository: LLMRepository | None = None,
    ) -> None:
        self._analytics_repository = analytics_repository
        self._llm_repository = llm_repository

    @staticmethod
    def _sanitize_scenario(scenario: str) -> str:
        """Strip whitespace, collapse runs of whitespace, and remove control characters."""
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", scenario)
        sanitized = re.sub(r"\s+", " ", sanitized)
        return sanitized.strip()

    def select_securities_for_scenario(
        self,
        scenario_description: str,
        num_selections: int = 10,
    ) -> ScenarioSelectionResponse:
        """
        Select securities that would perform well in the given scenario.

        Args:
            scenario_description: Natural language description of the scenario
                (e.g., "Rising inflation with Fed rate hikes", "Tech bubble burst",
                "Stagflation environment", "War in Eastern Europe")
            num_selections: Target number of securities to select (default 10)

        Returns:
            ScenarioSelectionResponse with selected securities and analysis
        """
        if self._llm_repository is None:
            return ScenarioSelectionResponse(
                scenario_summary="LLM service not available",
                selections=[],
                scenario_risks=["LLM service not configured"],
                diversification_notes="",
                model_used="none",
                securities_analyzed=0,
            )

        # Sanitize input
        scenario_description = self._sanitize_scenario(scenario_description)

        if not scenario_description:
            return ScenarioSelectionResponse(
                scenario_summary="Empty scenario description provided",
                selections=[],
                scenario_risks=["No scenario to analyze"],
                diversification_notes="",
                model_used="none",
                securities_analyzed=0,
            )

        # Get enriched securities from analytics warehouse
        enriched_securities = self._analytics_repository.get_enriched_securities()

        if not enriched_securities:
            return ScenarioSelectionResponse(
                scenario_summary="No securities available for analysis",
                selections=[],
                scenario_risks=["No securities data available - run data ingestion"],
                diversification_notes="",
                model_used="none",
                securities_analyzed=0,
            )

        # Convert to LLM-compatible format
        llm_securities = self._to_llm_format(enriched_securities)

        # Call LLM for scenario analysis
        result: ScenarioAnalysisResult = (
            self._llm_repository.select_securities_for_scenario(
                scenario_description=scenario_description,
                available_securities=llm_securities,
                num_selections=num_selections,
            )
        )

        # Build lookup map for enriched data
        security_map = {s.ticker.upper(): s for s in enriched_securities}

        # Convert result to response format with enriched data
        selections = []
        for sel in result.selections:
            enriched = security_map.get(sel.ticker.upper())
            selections.append(
                SelectedSecurity(
                    ticker=sel.ticker,
                    display_name=sel.display_name,
                    weight=sel.weight,
                    rationale=sel.rationale,
                    expected_behavior=sel.expected_behavior,
                    sector=enriched.sector if enriched else None,
                    market_cap_category=enriched.market_cap_category if enriched else None,
                    beta=enriched.beta if enriched else None,
                    dividend_yield=enriched.dividend_yield if enriched else None,
                )
            )

        return ScenarioSelectionResponse(
            scenario_summary=result.scenario_summary,
            selections=selections,
            scenario_risks=result.scenario_risks,
            diversification_notes=result.diversification_notes,
            model_used=result.model_used,
            securities_analyzed=len(enriched_securities),
        )

    def _to_llm_format(
        self, securities: list[EnrichedSecurity]
    ) -> list[EnrichedSecuritySummary]:
        """Convert EnrichedSecurity value objects to LLM-compatible format."""
        return [
            EnrichedSecuritySummary(
                ticker=s.ticker,
                display_name=s.display_name,
                asset_type=s.asset_type,
                sector=s.sector,
                industry=s.industry,
                market_cap=s.market_cap,
                market_cap_category=s.market_cap_category,
                beta=s.beta,
                trailing_pe=s.trailing_pe,
                forward_pe=s.forward_pe,
                price_to_book=s.price_to_book,
                dividend_yield=s.dividend_yield,
                profit_margin=s.profit_margin,
                return_on_equity=s.return_on_equity,
                revenue_growth=s.revenue_growth,
                debt_to_equity=s.debt_to_equity,
                is_dividend_payer=s.is_dividend_payer,
                is_high_growth=s.is_high_growth,
                is_value=s.is_value,
                is_defensive=s.is_defensive,
                is_cyclical=s.is_cyclical,
                is_rate_sensitive=s.is_rate_sensitive,
                is_inflation_hedge=s.is_inflation_hedge,
                historical_annual_return=s.historical_annual_return,
                annualized_volatility=s.annualized_volatility,
                analyst_implied_return=s.analyst_implied_return,
                analyst_count=s.analyst_count,
            )
            for s in securities
        ]

    def get_available_securities_count(self) -> int:
        """Get count of securities available for scenario selection."""
        return len(self._analytics_repository.get_enriched_securities())
