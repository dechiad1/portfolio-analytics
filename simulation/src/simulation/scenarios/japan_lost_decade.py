"""Japan Lost Decade scenario - prolonged low returns and deflation."""

import numpy as np
from numpy.typing import NDArray

from simulation.types import SimulationParams, State


class JapanLostDecadeScenario:
    """Simulates Japan's Lost Decade conditions.

    Key characteristics:
    - Significantly reduced expected returns
    - Prolonged period of underperformance
    - Equity markets that fail to recover

    Historical context: Japan's Nikkei peaked in 1989 and took
    over 30 years to recover. This scenario models similar
    conditions where expected returns are dramatically lower.
    """

    def __init__(
        self,
        mu_reduction_factor: float = 0.2,
        equity_penalty: float = 0.3,
    ) -> None:
        """Initialize Japan Lost Decade scenario.

        Args:
            mu_reduction_factor: Factor to reduce all expected returns (0.2 = 80% reduction)
            equity_penalty: Additional reduction for equities
        """
        self._mu_reduction = mu_reduction_factor
        self._equity_penalty = equity_penalty

    def apply(
        self,
        params: SimulationParams,
        state: State,
        t: int,
    ) -> SimulationParams:
        """Apply Japan Lost Decade conditions to parameters.

        Reduces expected returns significantly, especially for equities.
        """
        # Reduce all expected returns
        reduced_mu = params.mu * self._mu_reduction

        # Apply additional penalty for positive-mu assets (likely equities)
        for i, mu in enumerate(params.mu):
            if mu > 0:
                reduced_mu[i] = mu * (self._mu_reduction - self._equity_penalty)

        # Ensure mu doesn't go excessively negative
        reduced_mu = np.maximum(reduced_mu, -0.10)

        return SimulationParams(
            tickers=params.tickers,
            weights=params.weights,
            mu=np.asarray(reduced_mu, dtype=np.float64),
            volatility=params.volatility,
            correlation_matrix=params.correlation_matrix,
            initial_portfolio_value=params.initial_portfolio_value,
        )

    def apply_shock(
        self,
        state: State,
        t: int,
    ) -> NDArray[np.floating] | None:
        """No one-time shocks in this scenario - it's gradual."""
        return None
