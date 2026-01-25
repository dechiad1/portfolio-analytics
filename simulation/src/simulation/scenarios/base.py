"""Base protocol for stress test scenarios."""

from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from simulation.types import SimulationParams, State


class Scenario(Protocol):
    """Protocol for stress test scenarios.

    Scenarios modify simulation parameters to model specific
    economic conditions or historical periods.
    """

    def apply(
        self,
        params: SimulationParams,
        state: State,
        t: int,
    ) -> SimulationParams:
        """Apply scenario modifications to parameters.

        Args:
            params: Base simulation parameters
            state: Current simulation state
            t: Current time step

        Returns:
            Modified parameters for this step
        """
        ...

    def apply_shock(
        self,
        state: State,
        t: int,
    ) -> NDArray[np.floating] | None:
        """Apply a one-time shock to returns.

        Args:
            state: Current simulation state
            t: Current time step

        Returns:
            Shock returns to add, or None if no shock
        """
        ...
