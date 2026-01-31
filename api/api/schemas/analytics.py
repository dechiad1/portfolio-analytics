from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class TickerSearchResult(BaseModel):
    """Response schema for ticker search result."""

    ticker: str
    name: str
    asset_class: str
    category: str | None = None


class TickerSearchResponse(BaseModel):
    """Response schema for ticker search."""

    results: list[TickerSearchResult]
    count: int


class TickerAnalyticsResponse(BaseModel):
    """Response schema for individual ticker analytics."""

    ticker: str
    name: str
    asset_class: str
    sector: str
    total_return_pct: float
    annualized_return_pct: float
    volatility_pct: float
    sharpe_ratio: float
    vs_benchmark_pct: float
    expense_ratio: float | None = None


class AssetClassBreakdownResponse(BaseModel):
    """Response schema for asset class breakdown."""

    asset_class: str
    count: int
    avg_return: float


class SectorBreakdownResponse(BaseModel):
    """Response schema for sector breakdown."""

    sector: str
    count: int
    avg_return: float


class AnalyticsResponse(BaseModel):
    """Response schema for portfolio analytics."""

    holdings_count: int
    avg_total_return_pct: float
    avg_annualized_return_pct: float
    avg_sharpe_ratio: float
    beat_benchmark_count: int
    holdings: list[TickerAnalyticsResponse]
    asset_class_breakdown: list[AssetClassBreakdownResponse]
    sector_breakdown: list[SectorBreakdownResponse]


class SecurityResponse(BaseModel):
    """Response schema for a security with performance data."""

    ticker: str
    name: str
    asset_class: str
    category: str | None = None
    expense_ratio: float | None = None
    # 1-Year metrics
    total_return_1y_pct: float | None = None
    return_vs_risk_free_1y_pct: float | None = None
    return_vs_sp500_1y_pct: float | None = None
    volatility_1y_pct: float | None = None
    sharpe_ratio_1y: float | None = None
    # 5-Year metrics
    total_return_5y_pct: float | None = None
    return_vs_risk_free_5y_pct: float | None = None
    return_vs_sp500_5y_pct: float | None = None
    volatility_5y_pct: float | None = None
    sharpe_ratio_5y: float | None = None


class SecuritiesListResponse(BaseModel):
    """Response schema for a list of securities."""

    securities: list[SecurityResponse]
    count: int


class TickerDetailsResponse(BaseModel):
    """Response schema for ticker details with pricing data."""

    ticker: str
    name: str
    asset_class: str
    sector: str | None = None
    category: str | None = None
    latest_price: float | None = None
    latest_price_date: date | None = None


class TickerPriceResponse(BaseModel):
    """Response schema for ticker price at a specific date."""

    ticker: str
    price_date: date
    price: float


# =============================================================================
# SCENARIO SELECTION SCHEMAS
# =============================================================================


class ScenarioSelectionRequest(BaseModel):
    """Request schema for scenario-based securities selection."""

    scenario: str
    """
    Natural language description of the economic/policy scenario.
    Examples:
    - "Rising inflation with Fed rate hikes"
    - "Tech bubble burst, flight to safety"
    - "Stagflation environment with high unemployment"
    - "War in Eastern Europe, energy crisis"
    - "Strong economic growth, bull market"
    """
    num_selections: int = 10
    """Target number of securities to select (default 10, max 25)."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scenario": "Rising inflation with persistent Fed rate hikes, recession fears growing",
                    "num_selections": 10,
                },
                {
                    "scenario": "Tech bubble burst, investors flee to safety and value",
                    "num_selections": 8,
                },
            ]
        }
    }


class SelectedSecurityResponse(BaseModel):
    """Response schema for a security selected for a scenario."""

    ticker: str
    display_name: str
    weight: float
    """Suggested weight in the portfolio (0-100)."""
    rationale: str
    """Why this security fits the scenario."""
    expected_behavior: str
    """How it's expected to perform in the scenario."""
    sector: str | None = None
    market_cap_category: str | None = None
    beta: float | None = None
    dividend_yield: float | None = None


class ScenarioSelectionResponse(BaseModel):
    """Response schema for scenario-based securities selection."""

    scenario_summary: str
    """LLM's interpretation and summary of the scenario."""
    selections: list[SelectedSecurityResponse]
    """List of securities selected for the scenario with weights and rationale."""
    scenario_risks: list[str]
    """Risks specific to this scenario-based selection."""
    diversification_notes: str
    """Notes on diversification of the selection."""
    model_used: str
    """LLM model used for the analysis."""
    securities_analyzed: int
    """Number of securities available for selection."""
