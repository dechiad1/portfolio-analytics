"""Transaction costs and market frictions."""


class TransactionCosts:
    """Calculates transaction costs for portfolio trades."""

    def __init__(self, cost_bps: float = 10.0) -> None:
        """Initialize transaction costs.

        Args:
            cost_bps: Transaction cost in basis points (10 = 0.10%)
        """
        self._cost_rate = cost_bps / 10000.0

    def calculate_cost(
        self,
        portfolio_value: float,
        turnover: float,
    ) -> float:
        """Calculate transaction cost for a rebalancing event.

        Args:
            portfolio_value: Current portfolio value
            turnover: Fraction of portfolio traded (0-1)

        Returns:
            Total transaction cost in currency units
        """
        traded_value = portfolio_value * turnover
        return traded_value * self._cost_rate
