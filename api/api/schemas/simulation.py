"""Request/response schemas for portfolio simulation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    """Return model types for simulation."""

    GAUSSIAN = "gaussian"
    STUDENT_T = "student_t"
    REGIME_SWITCHING = "regime_switching"


class MuType(str, Enum):
    """Expected return calculation method."""

    HISTORICAL = "historical"
    FORWARD = "forward"


class ScenarioType(str, Enum):
    """Stress test scenario types."""

    JAPAN_LOST_DECADE = "japan_lost_decade"
    STAGFLATION = "stagflation"


class RebalanceFrequency(str, Enum):
    """Portfolio rebalancing frequency."""

    QUARTERLY = "quarterly"
    MONTHLY = "monthly"


class RuinThresholdType(str, Enum):
    """Type of ruin threshold specification."""

    PERCENTAGE = "percentage"
    ABSOLUTE = "absolute"


class SimulationRequest(BaseModel):
    """Request schema for running a portfolio simulation."""

    name: str | None = Field(
        default=None,
        max_length=255,
        description="Optional custom name for the simulation",
    )
    horizon_years: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Simulation horizon in years (max 30)",
    )
    num_paths: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Number of Monte Carlo paths (max 10,000)",
    )
    model_type: ModelType = Field(
        default=ModelType.GAUSSIAN,
        description="Return model type",
    )
    scenario: ScenarioType | None = Field(
        default=None,
        description="Stress test scenario to apply",
    )
    rebalance_frequency: RebalanceFrequency | None = Field(
        default=None,
        description="Portfolio rebalancing frequency",
    )
    mu_type: MuType = Field(
        default=MuType.HISTORICAL,
        description="Source for expected returns",
    )
    sample_paths_count: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of representative paths to return (max 50)",
    )
    ruin_threshold: float | None = Field(
        default=None,
        description="Threshold for probability of ruin calculation",
    )
    ruin_threshold_type: RuinThresholdType = Field(
        default=RuinThresholdType.PERCENTAGE,
        description="Whether ruin_threshold is a percentage loss or absolute value",
    )


class SamplePathResponse(BaseModel):
    """A single representative simulation path."""

    percentile: int = Field(description="Percentile this path represents")
    values: list[float] = Field(description="Portfolio value at each time step")
    terminal_value: float = Field(description="Final portfolio value")


class MetricsSummaryResponse(BaseModel):
    """Summary statistics from simulation results."""

    terminal_wealth_mean: float = Field(description="Mean terminal portfolio value")
    terminal_wealth_median: float = Field(description="Median terminal portfolio value")
    terminal_wealth_percentiles: dict[int, float] = Field(
        description="Terminal value at key percentiles (5, 25, 75, 95)"
    )
    max_drawdown_mean: float = Field(description="Mean maximum drawdown")
    max_drawdown_percentiles: dict[int, float] = Field(
        description="Max drawdown at key percentiles"
    )
    cvar_95: float = Field(description="Conditional Value at Risk (5% tail)")
    probability_of_ruin: float = Field(
        description="Probability of falling below ruin threshold"
    )
    ruin_threshold: float | None = Field(description="User-specified ruin threshold")
    ruin_threshold_type: str = Field(description="Type of ruin threshold")


class SimulationResponse(BaseModel):
    """Full response schema for a saved simulation."""

    id: UUID = Field(description="Simulation ID")
    portfolio_id: UUID = Field(description="Portfolio ID")
    name: str | None = Field(description="User-provided name")
    horizon_years: int = Field(description="Simulation horizon in years")
    num_paths: int = Field(description="Number of Monte Carlo paths")
    model_type: ModelType = Field(description="Return model type")
    scenario: ScenarioType | None = Field(description="Stress test scenario")
    rebalance_frequency: RebalanceFrequency | None = Field(description="Rebalancing frequency")
    mu_type: MuType = Field(description="Expected return source")
    sample_paths_count: int = Field(description="Number of sample paths returned")
    ruin_threshold: float | None = Field(description="Ruin threshold value")
    ruin_threshold_type: RuinThresholdType = Field(description="Ruin threshold type")
    metrics: MetricsSummaryResponse = Field(description="Summary statistics")
    sample_paths: list[SamplePathResponse] = Field(
        description="Representative paths at evenly-spaced percentiles"
    )
    created_at: datetime = Field(description="When simulation was created")


class SimulationSummaryResponse(BaseModel):
    """Summary response for list view (no sample_paths)."""

    id: UUID = Field(description="Simulation ID")
    portfolio_id: UUID = Field(description="Portfolio ID")
    name: str | None = Field(description="User-provided name")
    horizon_years: int = Field(description="Simulation horizon in years")
    num_paths: int = Field(description="Number of Monte Carlo paths")
    model_type: ModelType = Field(description="Return model type")
    scenario: ScenarioType | None = Field(description="Stress test scenario")
    mu_type: MuType = Field(description="Expected return source")
    metrics: MetricsSummaryResponse = Field(description="Summary statistics")
    created_at: datetime = Field(description="When simulation was created")


class SimulationRenameRequest(BaseModel):
    """Request schema for renaming a simulation."""

    name: str = Field(max_length=255, description="New simulation name")
