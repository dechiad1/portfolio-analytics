from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class Simulation(BaseModel):
    """Represents a saved portfolio simulation with results."""

    id: UUID
    portfolio_id: UUID
    name: str | None
    # Request params
    horizon_years: int
    num_paths: int
    model_type: str
    scenario: str | None
    rebalance_frequency: str | None
    mu_type: str
    sample_paths_count: int
    ruin_threshold: float | None
    ruin_threshold_type: str
    # Results
    metrics: dict[str, Any]
    sample_paths: list[dict[str, Any]]
    # Timestamps
    created_at: datetime

    model_config = {"frozen": True}
