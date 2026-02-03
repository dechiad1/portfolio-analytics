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
    TransactionInput,
)
from domain.ports.unit_of_work import TransactionContext, UnitOfWork
from domain.services.portfolio_builder_service import PortfolioAllocation, AllocationItem


@dataclass
class CreatePortfolioResult:
    """Result of creating a portfolio with holdings."""

    portfolio: Portfolio
    holdings_created: int
    unmatched_descriptions: list[str]


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

        today = date.today()

        # Create position
        self._portfolio_builder_repository.create_position_in_transaction(
            ctx=ctx,
            position=PositionInput(
                portfolio_id=portfolio_id,
                security_id=security_id,
                quantity=quantity,
                avg_cost=price,
            ),
        )

        # Create BUY transaction for audit trail
        self._portfolio_builder_repository.create_transaction_in_transaction(
            ctx=ctx,
            transaction=TransactionInput(
                txn_id=uuid4(),
                portfolio_id=portfolio_id,
                security_id=security_id,
                txn_type="BUY",
                quantity=quantity,
                price=price,
                event_ts=today,
            ),
        )
