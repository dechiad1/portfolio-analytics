import yfinance as yf

from domain.ports.ticker_validator import TickerValidator, ValidatedTicker


class YFinanceTickerValidator(TickerValidator):
    """yfinance implementation of TickerValidator."""

    def validate(self, ticker: str) -> ValidatedTicker | None:
        """Validate ticker via Yahoo Finance API."""
        try:
            ticker_upper = ticker.upper().strip()
            ticker_obj = yf.Ticker(ticker_upper)
            info = ticker_obj.info

            # Check if valid (has price data)
            if not info.get("regularMarketPrice") and not info.get("previousClose"):
                return None

            # Map yfinance quoteType to our asset_type
            quote_type = info.get("quoteType", "EQUITY")
            asset_type = "EQUITY"
            if quote_type == "ETF":
                asset_type = "ETF"

            return ValidatedTicker(
                ticker=ticker_upper,
                display_name=info.get("longName")
                or info.get("shortName")
                or ticker_upper,
                asset_type=asset_type,
                exchange=info.get("exchange"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                currency=info.get("currency", "USD"),
            )
        except Exception:
            return None
