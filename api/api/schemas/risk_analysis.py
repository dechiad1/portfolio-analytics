from pydantic import BaseModel


class RiskItem(BaseModel):
    """Individual risk item in the analysis."""

    category: str
    severity: str
    title: str
    description: str
    affected_holdings: list[str]
    potential_impact: str
    mitigation: str


class RiskAnalysisResponse(BaseModel):
    """Response schema for portfolio risk analysis."""

    risks: list[RiskItem]
    macro_climate_summary: str
    analysis_timestamp: str
    model_used: str
