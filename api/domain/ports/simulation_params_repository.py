"""Port for fetching simulation parameters from the data warehouse."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class SecuritySimParams:
    """Simulation parameters for a single security."""

    ticker: str
    historical_mu: float | None
    forward_mu: float | None
    volatility: float | None


@dataclass
class HistoricalReturns:
    """Historical daily returns for correlation calculation."""

    ticker: str
    dates: list[str]
    returns: list[float]


class SimulationParamsRepository(ABC):
    """Port for fetching simulation parameters from the data warehouse."""

    @abstractmethod
    def get_security_params(self, tickers: list[str]) -> list[SecuritySimParams]:
        """Fetch mu and volatility for the given securities.

        Args:
            tickers: List of ticker symbols

        Returns:
            List of SecuritySimParams with mu/vol data
        """
        pass

    @abstractmethod
    def get_historical_returns(
        self, tickers: list[str]
    ) -> dict[str, NDArray[np.floating]]:
        """Fetch historical daily returns for correlation calculation.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker to array of daily returns
        """
        pass
