from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from domain.models.holding import Holding
from domain.models.portfolio import Portfolio
from domain.ports.analytics_repository import AnalyticsRepository
from domain.services.portfolio_builder_service import PortfolioAllocation, AllocationItem
from adapters.postgres.connection import PostgresConnectionPool


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
        postgres_pool: PostgresConnectionPool,
        analytics_repository: AnalyticsRepository,
    ) -> None:
        self._pool = postgres_pool
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
        now = datetime.now(timezone.utc)
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

        with self._pool.transaction() as cur:
            # Create the portfolio
            cur.execute(
                """
                INSERT INTO portfolio (portfolio_id, user_id, name, base_currency, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING portfolio_id, user_id, name, base_currency, created_at, updated_at
                """,
                (portfolio_id, user_id, name, base_currency, now, now),
            )
            portfolio_row = cur.fetchone()

            if portfolio_row is None:
                raise RuntimeError("Failed to create portfolio")

            # Create holdings if allocation is provided
            if allocation and allocation.allocations:
                for item in allocation.allocations:
                    try:
                        self._create_holding_in_transaction(
                            cur=cur,
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
        cur,
        portfolio_id: UUID,
        item: AllocationItem,
        price: Decimal,
    ) -> None:
        """Create a single holding within an existing transaction."""
        # Check if security already exists
        cur.execute(
            """
            SELECT sr.security_id
            FROM security_registry sr
            JOIN equity_details ed ON sr.security_id = ed.security_id
            WHERE ed.ticker = %s
            """,
            (item.ticker,),
        )
        row = cur.fetchone()

        if row:
            security_id = row[0]
        else:
            # Create new security
            security_id = uuid4()
            asset_type = item.asset_type.upper()
            if asset_type not in ("EQUITY", "ETF", "BOND", "CASH"):
                asset_type = "EQUITY"

            cur.execute(
                """
                INSERT INTO security_registry (security_id, asset_type, currency, display_name, is_active)
                VALUES (%s, %s::asset_type, 'USD', %s, true)
                """,
                (security_id, asset_type, item.display_name),
            )

            cur.execute(
                """
                INSERT INTO equity_details (security_id, ticker, sector)
                VALUES (%s, %s, %s)
                """,
                (security_id, item.ticker, item.sector),
            )

            cur.execute(
                """
                INSERT INTO security_identifier (security_id, id_type, id_value, is_primary)
                VALUES (%s, 'TICKER'::identifier_type, %s, true)
                """,
                (security_id, item.ticker),
            )

        # Calculate quantity from value and price
        quantity = (item.value / price).quantize(Decimal("0.0001")) if price > 0 else Decimal("0")

        # Map sector to asset class
        asset_class = map_sector_to_asset_class(item.sector, item.asset_type)

        # Create position
        cur.execute(
            """
            INSERT INTO position_current (
                portfolio_id, security_id, quantity, avg_cost,
                broker, purchase_date, current_price, asset_class
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                portfolio_id,
                security_id,
                quantity,
                price,  # purchase_price = current price at creation
                "Generated",
                date.today(),
                price,
                asset_class,
            ),
        )
