"""Portfolio rebalancing logic."""

import numpy as np
from numpy.typing import NDArray

from simulation.types import SimulationParams, State


class Rebalancer:
    """Handles portfolio rebalancing with drift tolerance."""

    def __init__(
        self,
        threshold: float = 0.05,
        target_weights: NDArray[np.floating] | None = None,
    ) -> None:
        """Initialize rebalancer.

        Args:
            threshold: Maximum allowed drift before rebalancing (0.05 = 5%)
            target_weights: Target allocation weights. If None, uses initial weights.
        """
        self._threshold = threshold
        self._target_weights = target_weights

    def needs_rebalance(
        self,
        current_weights: NDArray[np.floating],
        target_weights: NDArray[np.floating] | None = None,
    ) -> bool:
        """Check if rebalancing is needed based on drift threshold.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target weights (uses stored target if None)

        Returns:
            True if any weight has drifted beyond threshold
        """
        targets = target_weights if target_weights is not None else self._target_weights
        if targets is None:
            return False

        max_drift = np.max(np.abs(current_weights - targets))
        return float(max_drift) > self._threshold

    def rebalance(
        self,
        state: State,
        params: SimulationParams,
    ) -> tuple[NDArray[np.floating], float]:
        """Rebalance portfolio to target weights.

        Args:
            state: Current simulation state
            params: Simulation parameters containing target weights

        Returns:
            Tuple of (new_weights, turnover) where turnover is the
            fraction of portfolio traded
        """
        target_weights = params.weights
        current_weights = state.current_weights

        # Calculate turnover (sum of absolute weight changes / 2)
        turnover = float(np.sum(np.abs(target_weights - current_weights)) / 2)

        return target_weights.copy(), turnover
