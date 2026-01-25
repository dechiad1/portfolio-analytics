"""Regime-switching return model with calm and crisis states."""

import numpy as np
from numpy.random import Generator
from numpy.typing import NDArray
from scipy import linalg

from simulation.types import Regime, SimulationParams, State


class RegimeSwitchingModel:
    """Two-regime switching model (calm and crisis).

    In crisis regime:
    - Volatility is scaled up
    - Expected returns are reduced
    - Correlations increase toward 1 (contagion effect)

    Transitions follow a Markov chain with specified probabilities.
    """

    def __init__(
        self,
        calm_to_crisis_prob: float = 0.05,
        crisis_to_calm_prob: float = 0.20,
        crisis_vol_multiplier: float = 2.0,
        crisis_mu_reduction: float = 0.5,
        crisis_correlation_floor: float = 0.7,
        steps_per_year: int = 4,
    ) -> None:
        """Initialize the regime-switching model.

        Args:
            calm_to_crisis_prob: Probability of transitioning from calm to crisis
            crisis_to_calm_prob: Probability of transitioning from crisis to calm
            crisis_vol_multiplier: Multiplier for volatility in crisis
            crisis_mu_reduction: Factor to reduce mu in crisis (0.5 = halve returns)
            crisis_correlation_floor: Minimum correlation in crisis
            steps_per_year: Number of simulation steps per year
        """
        self._p_calm_to_crisis = calm_to_crisis_prob
        self._p_crisis_to_calm = crisis_to_calm_prob
        self._crisis_vol_mult = crisis_vol_multiplier
        self._crisis_mu_reduction = crisis_mu_reduction
        self._crisis_corr_floor = crisis_correlation_floor
        self._steps_per_year = steps_per_year

    def _transition_regime(self, current: Regime, rng: Generator) -> Regime:
        """Determine next regime based on transition probabilities."""
        u = rng.uniform()
        if current == Regime.CALM:
            return Regime.CRISIS if u < self._p_calm_to_crisis else Regime.CALM
        else:
            return Regime.CALM if u < self._p_crisis_to_calm else Regime.CRISIS

    def _apply_crisis_correlation(
        self,
        corr_matrix: NDArray[np.floating],
    ) -> NDArray[np.floating]:
        """Increase correlations toward 1 during crisis (contagion)."""
        n = corr_matrix.shape[0]
        crisis_corr = corr_matrix.copy()

        # Move off-diagonal elements toward crisis floor
        for i in range(n):
            for j in range(n):
                if i != j:
                    crisis_corr[i, j] = max(
                        corr_matrix[i, j],
                        self._crisis_corr_floor,
                    )

        return crisis_corr

    def sample_returns(
        self,
        state: State,
        params: SimulationParams,
        t: int,
        rng: Generator,
    ) -> NDArray[np.floating]:
        """Sample returns based on current regime."""
        n_assets = params.n_assets
        regime = state.current_regime

        # Base parameters scaled to step frequency
        step_mu = params.mu / self._steps_per_year
        step_vol = params.volatility / np.sqrt(self._steps_per_year)

        # Apply regime adjustments
        if regime == Regime.CRISIS:
            step_mu = step_mu * self._crisis_mu_reduction
            step_vol = step_vol * self._crisis_vol_mult
            corr_matrix = self._apply_crisis_correlation(params.correlation_matrix)
        else:
            corr_matrix = params.correlation_matrix

        # Build covariance matrix
        vol_diag = np.diag(step_vol)
        step_cov = vol_diag @ corr_matrix @ vol_diag

        # Ensure positive definiteness
        try:
            chol = linalg.cholesky(step_cov, lower=True)
        except linalg.LinAlgError:
            step_cov_fixed = step_cov + np.eye(n_assets) * 1e-6
            chol = linalg.cholesky(step_cov_fixed, lower=True)

        # Sample returns
        z = rng.standard_normal(n_assets)
        returns = step_mu + chol @ z

        return np.asarray(returns, dtype=np.float64)

    def update_state(
        self,
        state: State,
        returns: NDArray[np.floating],
        rng: Generator | None = None,
    ) -> State:
        """Update state including potential regime transition."""
        # Update weights based on returns
        new_values = state.current_weights * (1 + returns)
        total = new_values.sum()
        new_weights = new_values / total if total > 0 else state.current_weights

        # Update portfolio value
        portfolio_return = np.dot(state.current_weights, returns)
        new_value = state.portfolio_value * (1 + portfolio_return)

        # Transition regime if rng provided
        if rng is not None:
            new_regime = self._transition_regime(state.current_regime, rng)
        else:
            new_regime = state.current_regime

        return State(
            current_weights=new_weights,
            portfolio_value=new_value,
            current_regime=new_regime,
            step=state.step + 1,
        )
