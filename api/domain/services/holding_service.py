import csv
from datetime import date, datetime, timezone
from decimal import Decimal
from io import StringIO
from uuid import UUID, uuid4

from domain.models.holding import Holding
from domain.ports.holding_repository import HoldingRepository


class HoldingValidationError(Exception):
    """Raised when holding data is invalid."""
    pass


class HoldingNotFoundError(Exception):
    """Raised when a holding is not found."""
    pass


class HoldingService:
    """Service for managing portfolio holdings."""

    REQUIRED_CSV_COLUMNS = {
        "ticker",
        "name",
        "asset_type",
        "asset_class",
        "sector",
        "broker",
        "quantity",
        "purchase_price",
        "purchase_date",
    }

    VALID_ASSET_TYPES = {"equity", "bond", "etf", "mutual_fund", "cash"}

    def __init__(self, holding_repository: HoldingRepository) -> None:
        self._repository = holding_repository

    def create_holding(
        self,
        portfolio_id: UUID,
        ticker: str,
        name: str,
        asset_type: str,
        asset_class: str,
        sector: str,
        broker: str,
        quantity: Decimal,
        purchase_price: Decimal,
        purchase_date: date,
        current_price: Decimal | None = None,
    ) -> Holding:
        """Create a new holding."""
        self._validate_holding_data(
            ticker, name, asset_type, asset_class, sector, broker, quantity, purchase_price
        )

        holding = Holding(
            id=uuid4(),
            portfolio_id=portfolio_id,
            ticker=ticker.upper().strip(),
            name=name.strip(),
            asset_type=asset_type.lower().strip(),
            asset_class=asset_class.strip(),
            sector=sector.strip(),
            broker=broker.strip(),
            quantity=quantity,
            purchase_price=purchase_price,
            current_price=current_price,
            purchase_date=purchase_date,
            created_at=datetime.now(timezone.utc),
        )
        return self._repository.create(holding)

    def get_holding(self, holding_id: UUID) -> Holding | None:
        """Retrieve a holding by ID."""
        return self._repository.get_by_id(holding_id)

    def get_holdings_for_portfolio(self, portfolio_id: UUID) -> list[Holding]:
        """Retrieve all holdings for a portfolio."""
        return self._repository.get_by_portfolio_id(portfolio_id)

    def get_all_holdings(self) -> list[Holding]:
        """Retrieve all holdings."""
        return self._repository.get_all()

    def update_holding(
        self,
        holding_id: UUID,
        ticker: str | None = None,
        name: str | None = None,
        asset_type: str | None = None,
        asset_class: str | None = None,
        sector: str | None = None,
        broker: str | None = None,
        quantity: Decimal | None = None,
        purchase_price: Decimal | None = None,
        current_price: Decimal | None = None,
        purchase_date: date | None = None,
    ) -> Holding:
        """Update an existing holding."""
        existing = self._repository.get_by_id(holding_id)
        if existing is None:
            raise HoldingNotFoundError(f"Holding {holding_id} not found")

        updated = Holding(
            id=existing.id,
            portfolio_id=existing.portfolio_id,
            ticker=(ticker.upper().strip() if ticker else existing.ticker),
            name=(name.strip() if name else existing.name),
            asset_type=(asset_type.lower().strip() if asset_type else existing.asset_type),
            asset_class=(asset_class.strip() if asset_class else existing.asset_class),
            sector=(sector.strip() if sector else existing.sector),
            broker=(broker.strip() if broker else existing.broker),
            quantity=(quantity if quantity is not None else existing.quantity),
            purchase_price=(purchase_price if purchase_price is not None else existing.purchase_price),
            current_price=(current_price if current_price is not None else existing.current_price),
            purchase_date=(purchase_date if purchase_date else existing.purchase_date),
            created_at=existing.created_at,
        )
        return self._repository.update(updated)

    def delete_holding(self, holding_id: UUID) -> None:
        """Delete a holding."""
        existing = self._repository.get_by_id(holding_id)
        if existing is None:
            raise HoldingNotFoundError(f"Holding {holding_id} not found")
        self._repository.delete(holding_id)

    def parse_and_create_holdings_from_csv(
        self, portfolio_id: UUID, csv_content: str
    ) -> list[Holding]:
        """Parse CSV content and create holdings in bulk."""
        holdings = self._parse_csv(portfolio_id, csv_content)
        return self._repository.bulk_create(holdings)

    def _parse_csv(self, portfolio_id: UUID, csv_content: str) -> list[Holding]:
        """Parse CSV content into Holding objects."""
        reader = csv.DictReader(StringIO(csv_content))

        if reader.fieldnames is None:
            raise HoldingValidationError("CSV file is empty or has no headers")

        normalized_headers = {h.lower().strip() for h in reader.fieldnames}
        missing_columns = self.REQUIRED_CSV_COLUMNS - normalized_headers
        if missing_columns:
            raise HoldingValidationError(
                f"CSV missing required columns: {', '.join(sorted(missing_columns))}"
            )

        header_map = {h.lower().strip(): h for h in reader.fieldnames}
        holdings: list[Holding] = []
        now = datetime.now(timezone.utc)

        for row_num, row in enumerate(reader, start=2):
            try:
                ticker = row[header_map["ticker"]].strip()
                name = row[header_map["name"]].strip()
                asset_type = row[header_map["asset_type"]].strip().lower()
                asset_class = row[header_map["asset_class"]].strip()
                sector = row[header_map["sector"]].strip()
                broker = row[header_map["broker"]].strip()
                quantity = Decimal(row[header_map["quantity"]].strip())
                purchase_price = Decimal(row[header_map["purchase_price"]].strip())
                purchase_date_str = row[header_map["purchase_date"]].strip()

                # Optional current_price
                current_price = None
                if "current_price" in header_map and row[header_map["current_price"]].strip():
                    current_price = Decimal(row[header_map["current_price"]].strip())

                self._validate_holding_data(
                    ticker, name, asset_type, asset_class, sector, broker, quantity, purchase_price
                )
                purchase_date = self._parse_date(purchase_date_str)

                holding = Holding(
                    id=uuid4(),
                    portfolio_id=portfolio_id,
                    ticker=ticker.upper(),
                    name=name,
                    asset_type=asset_type,
                    asset_class=asset_class,
                    sector=sector,
                    broker=broker,
                    quantity=quantity,
                    purchase_price=purchase_price,
                    current_price=current_price,
                    purchase_date=purchase_date,
                    created_at=now,
                )
                holdings.append(holding)

            except (KeyError, ValueError) as e:
                raise HoldingValidationError(f"Row {row_num}: {e}") from e

        if not holdings:
            raise HoldingValidationError("CSV contains no data rows")

        return holdings

    def _validate_holding_data(
        self,
        ticker: str,
        name: str,
        asset_type: str,
        asset_class: str,
        sector: str,
        broker: str,
        quantity: Decimal,
        purchase_price: Decimal,
    ) -> None:
        """Validate holding field values."""
        errors: list[str] = []

        if not ticker or not ticker.strip():
            errors.append("ticker cannot be empty")
        if not name or not name.strip():
            errors.append("name cannot be empty")
        if not asset_type or not asset_type.strip():
            errors.append("asset_type cannot be empty")
        elif asset_type.lower() not in self.VALID_ASSET_TYPES:
            errors.append(f"asset_type must be one of: {', '.join(self.VALID_ASSET_TYPES)}")
        if not asset_class or not asset_class.strip():
            errors.append("asset_class cannot be empty")
        if not sector or not sector.strip():
            errors.append("sector cannot be empty")
        if not broker or not broker.strip():
            errors.append("broker cannot be empty")
        if quantity < 0:
            errors.append("quantity cannot be negative")
        if purchase_price < 0:
            errors.append("purchase_price cannot be negative")

        if errors:
            raise HoldingValidationError("; ".join(errors))

    def _parse_date(self, date_str: str) -> date:
        """Parse date string in YYYY-MM-DD format."""
        try:
            return date.fromisoformat(date_str)
        except ValueError as e:
            raise HoldingValidationError(
                f"Invalid date format '{date_str}', expected YYYY-MM-DD"
            ) from e
