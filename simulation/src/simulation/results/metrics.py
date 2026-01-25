"""Summary statistics and metrics calculation."""

import numpy as np
from numpy.typing import NDArray

from simulation.types import MetricsSummary, RuinThresholdType


def compute_metrics(
    terminal_values: NDArray[np.floating],
    max_drawdowns: NDArray[np.floating],
    initial_value: float,
    ruin_threshold: float | None,
    ruin_threshold_type: RuinThresholdType,
) -> MetricsSummary:
    """Compute summary statistics from simulation results.

    Args:
        terminal_values: Array of terminal portfolio values
        max_drawdowns: Array of maximum drawdowns per path
        initial_value: Initial portfolio value
        ruin_threshold: Threshold for probability of ruin
        ruin_threshold_type: Whether threshold is percentage or absolute

    Returns:
        MetricsSummary with all computed statistics
    """
    # Terminal wealth statistics
    terminal_mean = float(np.mean(terminal_values))
    terminal_median = float(np.median(terminal_values))
    terminal_percentiles = {
        5: float(np.percentile(terminal_values, 5)),
        25: float(np.percentile(terminal_values, 25)),
        75: float(np.percentile(terminal_values, 75)),
        95: float(np.percentile(terminal_values, 95)),
    }

    # Max drawdown statistics
    max_drawdown_mean = float(np.mean(max_drawdowns))
    max_drawdown_percentiles = {
        5: float(np.percentile(max_drawdowns, 5)),
        25: float(np.percentile(max_drawdowns, 25)),
        75: float(np.percentile(max_drawdowns, 75)),
        95: float(np.percentile(max_drawdowns, 95)),
    }

    # Conditional Value at Risk (CVaR) at 95%
    # Average of the worst 5% of outcomes
    sorted_terminals = np.sort(terminal_values)
    cutoff_idx = max(1, int(len(sorted_terminals) * 0.05))
    cvar_95 = float(np.mean(sorted_terminals[:cutoff_idx]))

    # Probability of ruin
    probability_of_ruin = 0.0
    if ruin_threshold is not None:
        if ruin_threshold_type == RuinThresholdType.PERCENTAGE:
            # Threshold is a percentage loss (e.g., 0.30 = 30% loss)
            ruin_level = initial_value * (1 - ruin_threshold)
        else:
            # Threshold is an absolute value
            ruin_level = ruin_threshold

        probability_of_ruin = float(np.mean(terminal_values < ruin_level))

    return MetricsSummary(
        terminal_wealth_mean=terminal_mean,
        terminal_wealth_median=terminal_median,
        terminal_wealth_percentiles=terminal_percentiles,
        max_drawdown_mean=max_drawdown_mean,
        max_drawdown_percentiles=max_drawdown_percentiles,
        cvar_95=cvar_95,
        probability_of_ruin=probability_of_ruin,
        ruin_threshold=ruin_threshold,
        ruin_threshold_type=ruin_threshold_type.value if isinstance(ruin_threshold_type, RuinThresholdType) else ruin_threshold_type,
    )
