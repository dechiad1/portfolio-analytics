from datetime import datetime
from uuid import UUID

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

    id: UUID
    risks: list[RiskItem]
    macro_climate_summary: str
    created_at: datetime
    model_used: str


class RiskAnalysisListItem(BaseModel):
    """Summary item for risk analysis list."""

    id: UUID
    created_at: datetime
    model_used: str
    risk_count: int


class RiskAnalysisListResponse(BaseModel):
    """Response schema for list of risk analyses."""

    analyses: list[RiskAnalysisListItem]
