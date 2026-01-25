import random
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from domain.models.security import Security
from domain.ports.ticker_repository import TickerRepository
from domain.ports.llm_repository import LLMRepository, SecuritySummary


@dataclass
class AllocationItem:
    """Represents a single allocation in a portfolio."""

    ticker: str
    display_name: str
    asset_type: str
    sector: str | None
    weight: Decimal  # Percentage (0-100)
    value: Decimal  # Dollar value


@dataclass
class PortfolioAllocation:
    """Represents the result of portfolio allocation."""

    allocations: list[AllocationItem]
    total_value: Decimal
    unmatched_descriptions: list[str]


class PortfolioBuilderService:
    """Service for building portfolios with random or dictation-based allocation."""

    def __init__(
        self,
        ticker_repository: TickerRepository,
        llm_repository: LLMRepository | None = None,
    ) -> None:
        self._ticker_repository = ticker_repository
        self._llm_repository = llm_repository

    def generate_random_allocation(
        self,
        total_value: Decimal,
        min_securities: int = 5,
        max_securities: int = 15,
    ) -> PortfolioAllocation:
        """
        Generate a random portfolio allocation.

        Args:
            total_value: Total portfolio value in base currency
            min_securities: Minimum number of securities to include
            max_securities: Maximum number of securities to include

        Returns:
            PortfolioAllocation with random allocations
        """
        securities = self._ticker_repository.get_all_securities()

        # Filter to eligible securities (EQUITY and ETF only)
        eligible = [s for s in securities if s.asset_type in ("EQUITY", "ETF")]

        if not eligible:
            return PortfolioAllocation(
                allocations=[],
                total_value=total_value,
                unmatched_descriptions=["No eligible securities found in registry"],
            )

        # Select random number of securities
        count = random.randint(min_securities, min(max_securities, len(eligible)))
        selected = random.sample(eligible, count)

        # Generate random weights using Dirichlet-like distribution
        # Each security gets at least 2%
        min_weight = Decimal("2")
        remaining = Decimal("100") - (min_weight * count)

        # Generate random portions for the remaining weight
        raw_weights = [random.random() for _ in range(count)]
        total_raw = sum(raw_weights)

        allocations = []
        for i, security in enumerate(selected):
            # Calculate weight: minimum + proportional share of remaining
            additional = Decimal(str(raw_weights[i] / total_raw)) * remaining
            weight = min_weight + additional.quantize(Decimal("0.01"))

            # Calculate value
            value = (weight / Decimal("100")) * total_value

            allocations.append(
                AllocationItem(
                    ticker=security.ticker,
                    display_name=security.display_name,
                    asset_type=security.asset_type,
                    sector=security.sector,
                    weight=weight.quantize(Decimal("0.01")),
                    value=value.quantize(Decimal("0.01")),
                )
            )

        # Normalize weights to exactly 100%
        total_weight = sum(a.weight for a in allocations)
        if total_weight != Decimal("100"):
            diff = Decimal("100") - total_weight
            allocations[0] = AllocationItem(
                ticker=allocations[0].ticker,
                display_name=allocations[0].display_name,
                asset_type=allocations[0].asset_type,
                sector=allocations[0].sector,
                weight=(allocations[0].weight + diff).quantize(Decimal("0.01")),
                value=allocations[0].value,
            )
            # Recalculate value for first allocation
            allocations[0] = AllocationItem(
                ticker=allocations[0].ticker,
                display_name=allocations[0].display_name,
                asset_type=allocations[0].asset_type,
                sector=allocations[0].sector,
                weight=allocations[0].weight,
                value=(allocations[0].weight / Decimal("100") * total_value).quantize(
                    Decimal("0.01")
                ),
            )

        return PortfolioAllocation(
            allocations=allocations,
            total_value=total_value,
            unmatched_descriptions=[],
        )

    def get_available_securities(self) -> list[Security]:
        """Get all available securities for allocation."""
        return self._ticker_repository.get_all_securities()

    def build_from_description(
        self,
        description: str,
        total_value: Decimal,
    ) -> PortfolioAllocation:
        """
        Build a portfolio allocation based on natural language description.

        Args:
            description: User's description of their portfolio
            total_value: Total portfolio value in base currency

        Returns:
            PortfolioAllocation with allocations based on description
        """
        if self._llm_repository is None:
            return PortfolioAllocation(
                allocations=[],
                total_value=total_value,
                unmatched_descriptions=["LLM service not available"],
            )

        securities = self._ticker_repository.get_all_securities()

        if not securities:
            return PortfolioAllocation(
                allocations=[],
                total_value=total_value,
                unmatched_descriptions=["No securities available in registry"],
            )

        # Convert securities to SecuritySummary for LLM
        security_summaries = [
            SecuritySummary(
                ticker=s.ticker,
                display_name=s.display_name,
                asset_type=s.asset_type,
                sector=s.sector,
            )
            for s in securities
        ]

        # Get interpretation from LLM
        interpretation = self._llm_repository.interpret_portfolio_description(
            description=description,
            available_securities=security_summaries,
        )

        # Build a lookup map for securities
        security_map = {s.ticker.upper(): s for s in securities}

        allocations = []
        for interp in interpretation.allocations:
            ticker_upper = interp.ticker.upper()
            security = security_map.get(ticker_upper)

            if security:
                value = (interp.weight / Decimal("100")) * total_value
                allocations.append(
                    AllocationItem(
                        ticker=security.ticker,
                        display_name=security.display_name,
                        asset_type=security.asset_type,
                        sector=security.sector,
                        weight=interp.weight,
                        value=value.quantize(Decimal("0.01")),
                    )
                )
            else:
                interpretation.unmatched_descriptions.append(
                    f"Ticker {interp.ticker} not found in registry"
                )

        return PortfolioAllocation(
            allocations=allocations,
            total_value=total_value,
            unmatched_descriptions=interpretation.unmatched_descriptions,
        )
