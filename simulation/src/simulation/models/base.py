"""Base protocol for return models."""

from typing import Protocol

import numpy as np
from numpy.random import Generator
from numpy.typing import NDArray

from simulation.types import SimulationParams, State


class ReturnModel(Protocol):
    """Protocol for return-generating models.

    Each model implements how to sample returns for a single time step
    and how to update state between steps.
    """

    def sample_returns(
        self,
        state: State,
        params: SimulationParams,
        t: int,
        rng: Generator,
    ) -> NDArray[np.floating]:
        """Sample returns for all assets at time step t.

        Args:
            state: Current simulation state
            params: Simulation parameters (mu, cov, etc.)
            t: Current time step
            rng: Random number generator for reproducibility

        Returns:
            Array of returns for each asset
        """
        ...

    def update_state(
        self,
        state: State,
        returns: NDArray[np.floating],
    ) -> State:
        """Update state after observing returns.

        Args:
            state: Current simulation state
            returns: Observed returns for this step

        Returns:
            Updated state
        """
        ...
