"""Stagflation scenario - high inflation with economic stagnation."""

import numpy as np
from numpy.typing import NDArray

from simulation.types import SimulationParams, State


class StagflationScenario:
    """Simulates 1970s-style stagflation conditions.

    Key characteristics:
    - Elevated volatility
    - Reduced real returns
    - Increased correlations (diversification fails)

    Historical context: The 1970s saw high inflation combined
    with economic stagnation. Both stocks and bonds performed
    poorly in real terms. This scenario models similar conditions.
    """

    def __init__(
        self,
        volatility_multiplier: float = 1.5,
        mu_reduction_factor: float = 0.5,
        correlation_increase: float = 0.2,
    ) -> None:
        """Initialize stagflation scenario.

        Args:
            volatility_multiplier: Factor to increase volatility
            mu_reduction_factor: Factor to reduce expected returns
            correlation_increase: Amount to increase correlations
        """
        self._vol_mult = volatility_multiplier
        self._mu_reduction = mu_reduction_factor
        self._corr_increase = correlation_increase

    def apply(
        self,
        params: SimulationParams,
        state: State,
        t: int,
    ) -> SimulationParams:
        """Apply stagflation conditions to parameters.

        Increases volatility, reduces returns, and increases correlations.
        """
        # Reduce expected returns
        reduced_mu = params.mu * self._mu_reduction

        # Increase volatility
        increased_vol = params.volatility * self._vol_mult

        # Increase correlations (diversification breaks down)
        n = len(params.correlation_matrix)
        increased_corr = params.correlation_matrix.copy()
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Move correlation toward 1
                    increased_corr[i, j] = min(
                        increased_corr[i, j] + self._corr_increase,
                        0.95,
                    )

        return SimulationParams(
            tickers=params.tickers,
            weights=params.weights,
            mu=np.asarray(reduced_mu, dtype=np.float64),
            volatility=np.asarray(increased_vol, dtype=np.float64),
            correlation_matrix=np.asarray(increased_corr, dtype=np.float64),
            initial_portfolio_value=params.initial_portfolio_value,
        )

    def apply_shock(
        self,
        state: State,
        t: int,
    ) -> NDArray[np.floating] | None:
        """No one-time shocks in this scenario - it's persistent conditions."""
        return None
