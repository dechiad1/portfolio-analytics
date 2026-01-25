"""Student-t multivariate return model for fat-tailed distributions."""

import numpy as np
from numpy.random import Generator
from numpy.typing import NDArray
from scipy import linalg

from simulation.types import SimulationParams, State


class StudentTMVNModel:
    """Multivariate Student-t return model.

    Produces fat-tailed returns to better capture extreme market events.
    Uses degrees of freedom parameter to control tail heaviness.
    """

    def __init__(
        self,
        degrees_of_freedom: float = 5.0,
        steps_per_year: int = 4,
    ) -> None:
        """Initialize the Student-t model.

        Args:
            degrees_of_freedom: Controls tail heaviness (lower = fatter tails).
                Typical values: 3-10. Must be > 2 for finite variance.
            steps_per_year: Number of simulation steps per year
        """
        if degrees_of_freedom <= 2:
            raise ValueError("Degrees of freedom must be > 2 for finite variance")
        self._df = degrees_of_freedom
        self._steps_per_year = steps_per_year

    def sample_returns(
        self,
        state: State,
        params: SimulationParams,
        t: int,
        rng: Generator,
    ) -> NDArray[np.floating]:
        """Sample returns from multivariate Student-t distribution.

        Uses the representation: X = mu + Z * sqrt(df / chi2)
        where Z ~ MVN(0, Sigma) and chi2 ~ chi-squared(df).
        """
        n_assets = params.n_assets

        # Scale annualized parameters to step frequency
        step_mu = params.mu / self._steps_per_year
        step_cov = params.covariance_matrix / self._steps_per_year

        # Cholesky decomposition of covariance
        try:
            chol = linalg.cholesky(step_cov, lower=True)
        except linalg.LinAlgError:
            # If not positive definite, add small diagonal
            step_cov_fixed = step_cov + np.eye(n_assets) * 1e-6
            chol = linalg.cholesky(step_cov_fixed, lower=True)

        # Sample standard normal
        z = rng.standard_normal(n_assets)

        # Sample chi-squared for t-distribution scaling
        chi2 = rng.chisquare(self._df)
        scale = np.sqrt(self._df / chi2)

        # Construct multivariate t sample
        # Scale covariance for proper t variance: Var = cov * df / (df - 2)
        variance_adjustment = np.sqrt((self._df - 2) / self._df)
        returns = step_mu + (chol @ z) * scale * variance_adjustment

        return np.asarray(returns, dtype=np.float64)

    def update_state(
        self,
        state: State,
        returns: NDArray[np.floating],
    ) -> State:
        """Update state - Student-t model has no regime state to update."""
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
