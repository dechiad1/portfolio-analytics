from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class RiskAnalysis(BaseModel):
    """Represents a persisted portfolio risk analysis."""

    id: UUID
    portfolio_id: UUID
    risks: list[dict[str, Any]]
    macro_climate_summary: str
    model_used: str
    created_at: datetime

    model_config = {"frozen": True}
