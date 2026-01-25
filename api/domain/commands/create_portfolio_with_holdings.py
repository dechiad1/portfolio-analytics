from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from domain.models.portfolio import Portfolio
from domain.ports.analytics_repository import AnalyticsRepository
from domain.ports.portfolio_builder_repository import (
    PortfolioBuilderRepository,
    PositionInput,
    SecurityInput,
)
from domain.ports.unit_of_work import TransactionContext, UnitOfWork
from domain.services.portfolio_builder_service import PortfolioAllocation, AllocationItem


@dataclass
class CreatePortfolioResult:
    """Result of creating a portfolio with holdings."""

    portfolio: Portfolio
    holdings_created: int
    unmatched_descriptions: list[str]


# Mapping from sector to asset class
SECTOR_TO_ASSET_CLASS: dict[str, str] = {
    # U.S. Equity sectors
    "Technology": "U.S. Stocks",
    "Healthcare": "U.S. Stocks",
    "Financials": "U.S. Stocks",
    "Consumer Discretionary": "U.S. Stocks",
    "Consumer Staples": "U.S. Stocks",
    "Energy": "U.S. Stocks",
    "Materials": "U.S. Stocks",
    "Industrials": "U.S. Stocks",
    "Utilities": "U.S. Stocks",
    "Real Estate": "U.S. Stocks",
    "Communication Services": "U.S. Stocks",
    # Broad market / diversified
    "Broad Market": "U.S. Stocks",
    "Large Cap": "U.S. Stocks",
    "Mid Cap": "U.S. Stocks",
    "Small Cap": "U.S. Stocks",
    # International
    "International": "International Stocks",
    "Emerging Markets": "International Stocks",
    "Developed Markets": "International Stocks",
    "Europe": "International Stocks",
    "Asia Pacific": "International Stocks",
    "Latin America": "International Stocks",
    # Bonds
    "Bonds": "Bonds",
    "Government Bonds": "Bonds",
    "Corporate Bonds": "Bonds",
    "Municipal Bonds": "Bonds",
    "High Yield Bonds": "Bonds",
    "Treasury": "Bonds",
    # Other
    "Commodities": "Commodities",
    "Gold": "Commodities",
    "Oil & Gas": "Commodities",
    "Cash": "Cash & Equivalents",
    "Money Market": "Cash & Equivalents",
}


def map_sector_to_asset_class(sector: str | None, asset_type: str | None = None) -> str:
    """Map sector to asset class, considering asset type as fallback."""
    if sector:
        # Direct match
        if sector in SECTOR_TO_ASSET_CLASS:
            return SECTOR_TO_ASSET_CLASS[sector]
        # Case-insensitive match
        sector_lower = sector.lower()
        for key, value in SECTOR_TO_ASSET_CLASS.items():
            if key.lower() == sector_lower:
                return value

    # Fallback based on asset type
    if asset_type:
        asset_type_upper = asset_type.upper()
        if asset_type_upper == "BOND":
            return "Bonds"
        elif asset_type_upper == "CASH":
            return "Cash & Equivalents"
        elif asset_type_upper in ("EQUITY", "ETF"):
            return "U.S. Stocks"

    return "U.S. Stocks"  # Default


class CreatePortfolioWithHoldingsCommand:
    """
    Command to create a portfolio with holdings in a single transaction.

    This ensures atomicity - either the portfolio and all holdings are created,
    or none of them are (rollback on failure).
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        portfolio_builder_repository: PortfolioBuilderRepository,
        analytics_repository: AnalyticsRepository,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._portfolio_builder_repository = portfolio_builder_repository
        self._analytics_repository = analytics_repository

    def execute(
        self,
        user_id: UUID,
        name: str,
        base_currency: str,
        allocation: PortfolioAllocation | None = None,
    ) -> CreatePortfolioResult:
        """
        Create a portfolio and optionally populate it with holdings from an allocation.

        Args:
            user_id: Owner of the portfolio
            name: Portfolio name
            base_currency: Base currency (e.g., "USD")
            allocation: Optional allocation to create holdings from

        Returns:
            CreatePortfolioResult with the created portfolio and statistics
        """
        portfolio_id = uuid4()
        holdings_created = 0
        unmatched_descriptions: list[str] = []

        # Get prices for all tickers in the allocation
        price_map: dict[str, Decimal] = {}
        if allocation and allocation.allocations:
            for item in allocation.allocations:
                ticker_details = self._analytics_repository.get_ticker_details(item.ticker)
                if ticker_details and ticker_details.latest_price:
                    price_map[item.ticker] = ticker_details.latest_price
                else:
                    # Fallback to a default price if not available
                    price_map[item.ticker] = Decimal("100")
                    unmatched_descriptions.append(
                        f"Price not available for {item.ticker}, using default"
                    )

        with self._unit_of_work.transaction() as ctx:
            # Create the portfolio
            portfolio_row = self._portfolio_builder_repository.create_portfolio_in_transaction(
                ctx=ctx,
                portfolio_id=portfolio_id,
                user_id=user_id,
                name=name,
                base_currency=base_currency,
            )

            # Create holdings if allocation is provided
            if allocation and allocation.allocations:
                for item in allocation.allocations:
                    try:
                        self._create_holding_in_transaction(
                            ctx=ctx,
                            portfolio_id=portfolio_id,
                            item=item,
                            price=price_map.get(item.ticker, Decimal("100")),
                        )
                        holdings_created += 1
                    except Exception as e:
                        unmatched_descriptions.append(f"Failed to add {item.ticker}: {str(e)}")

            # Add any unmatched descriptions from the allocation
            if allocation:
                unmatched_descriptions.extend(allocation.unmatched_descriptions)

        portfolio = Portfolio(
            id=portfolio_row[0],
            user_id=portfolio_row[1],
            name=portfolio_row[2],
            base_currency=portfolio_row[3],
            created_at=portfolio_row[4],
            updated_at=portfolio_row[5],
        )

        return CreatePortfolioResult(
            portfolio=portfolio,
            holdings_created=holdings_created,
            unmatched_descriptions=unmatched_descriptions,
        )

    def _create_holding_in_transaction(
        self,
        ctx: TransactionContext,
        portfolio_id: UUID,
        item: AllocationItem,
        price: Decimal,
    ) -> None:
        """Create a single holding within an existing transaction."""
        # Check if security already exists
        security_id = self._portfolio_builder_repository.find_security_by_ticker(
            ctx=ctx,
            ticker=item.ticker,
        )

        if security_id is None:
            # Create new security
            security_id = uuid4()
            self._portfolio_builder_repository.create_security_in_transaction(
                ctx=ctx,
                security_id=security_id,
                security=SecurityInput(
                    ticker=item.ticker,
                    display_name=item.display_name,
                    asset_type=item.asset_type,
                    sector=item.sector,
                ),
            )

        # Calculate quantity from value and price
        quantity = (item.value / price).quantize(Decimal("0.0001")) if price > 0 else Decimal("0")

        # Map sector to asset class
        asset_class = map_sector_to_asset_class(item.sector, item.asset_type)

        # Create position
        self._portfolio_builder_repository.create_position_in_transaction(
            ctx=ctx,
            position=PositionInput(
                portfolio_id=portfolio_id,
                security_id=security_id,
                quantity=quantity,
                avg_cost=price,
                broker="Generated",
                purchase_date=date.today(),
                current_price=price,
                asset_class=asset_class,
            ),
        )
