"""Core types and dataclasses for the simulation engine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

import numpy as np
from numpy.typing import NDArray


class ModelType(str, Enum):
    """Return model types."""

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


class Regime(str, Enum):
    """Market regime states for regime-switching model."""

    CALM = "calm"
    CRISIS = "crisis"


@dataclass(frozen=True)
class SimulationParams:
    """Pre-computed parameters for simulation.

    These are fetched from the data warehouse before simulation runs.
    """

    tickers: tuple[str, ...]
    weights: NDArray[np.floating]
    mu: NDArray[np.floating]
    volatility: NDArray[np.floating]
    correlation_matrix: NDArray[np.floating]
    initial_portfolio_value: float

    @property
    def n_assets(self) -> int:
        return len(self.tickers)

    @property
    def covariance_matrix(self) -> NDArray[np.floating]:
        """Compute covariance matrix from volatility and correlation."""
        vol_diag = np.diag(self.volatility)
        return vol_diag @ self.correlation_matrix @ vol_diag


@dataclass
class State:
    """Mutable state persisted across simulation steps."""

    current_weights: NDArray[np.floating]
    portfolio_value: float
    current_regime: Regime = Regime.CALM
    step: int = 0


@dataclass(frozen=True)
class SimulationRequest:
    """Request for running a simulation."""

    params: SimulationParams
    steps: int
    num_paths: int
    model_type: ModelType = ModelType.GAUSSIAN
    scenario: ScenarioType | None = None
    rebalance_frequency: RebalanceFrequency | None = None
    rebalance_threshold: float = 0.05
    transaction_cost_bps: float = 10.0
    sample_paths_count: int = 10
    ruin_threshold: float | None = None
    ruin_threshold_type: RuinThresholdType = RuinThresholdType.PERCENTAGE
    seed: int | None = None


@dataclass(frozen=True)
class SamplePath:
    """A single representative simulation path."""

    percentile: int
    values: tuple[float, ...]
    terminal_value: float


@dataclass(frozen=True)
class MetricsSummary:
    """Summary statistics from simulation results."""

    terminal_wealth_mean: float
    terminal_wealth_median: float
    terminal_wealth_percentiles: dict[int, float]
    max_drawdown_mean: float
    max_drawdown_percentiles: dict[int, float]
    cvar_95: float
    probability_of_ruin: float
    ruin_threshold: float | None
    ruin_threshold_type: str


@dataclass
class SimulationResult:
    """Complete results from a simulation run."""

    metrics: MetricsSummary
    sample_paths: list[SamplePath]
    all_terminal_values: NDArray[np.floating] | None = None
