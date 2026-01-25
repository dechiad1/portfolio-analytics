"""Gaussian multivariate normal return model."""

import numpy as np
from numpy.random import Generator
from numpy.typing import NDArray

from simulation.types import SimulationParams, State


class GaussianMVNModel:
    """Multivariate Gaussian return model.

    Samples returns from a multivariate normal distribution
    with mean mu and covariance matrix derived from volatilities
    and correlations.
    """

    def __init__(self, steps_per_year: int = 4) -> None:
        """Initialize the Gaussian model.

        Args:
            steps_per_year: Number of simulation steps per year (default 4 for quarterly)
        """
        self._steps_per_year = steps_per_year

    def sample_returns(
        self,
        state: State,
        params: SimulationParams,
        t: int,
        rng: Generator,
    ) -> NDArray[np.floating]:
        """Sample returns from multivariate normal distribution.

        Scales annualized parameters to the step frequency.
        """
        # Scale annualized parameters to step frequency
        step_mu = params.mu / self._steps_per_year
        step_cov = params.covariance_matrix / self._steps_per_year

        # Sample from multivariate normal
        returns = rng.multivariate_normal(step_mu, step_cov)
        return np.asarray(returns, dtype=np.float64)

    def update_state(
        self,
        state: State,
        returns: NDArray[np.floating],
    ) -> State:
        """Update state - Gaussian model has no regime state to update."""
        # Update weights based on returns
        new_values = state.current_weights * (1 + returns)
        total = new_values.sum()
        new_weights = new_values / total if total > 0 else state.current_weights

        # Update portfolio value
        portfolio_return = np.dot(state.current_weights, returns)
        new_value = state.portfolio_value * (1 + portfolio_return)

        return State(
            current_weights=new_weights,
            portfolio_value=new_value,
            current_regime=state.current_regime,
            step=state.step + 1,
        )
