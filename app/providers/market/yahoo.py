from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from app.providers.market.base import MarketDataProvider
from app.providers.resilience import run_sync_with_retry


class YahooMarketProvider(MarketDataProvider):
    @property
    def provider_name(self) -> str:
        return "Yahoo Finance"

    @staticmethod
    def _fetch_latest_price(
        symbol: str,
    ) -> dict[str, Any]:
        ticker = yf.Ticker(
            symbol
        )

        history = ticker.history(
            period="1d"
        )

        if (
            history is None
            or history.empty
        ):
            raise ValueError(
                f"No market data found for {symbol}"
            )

        latest = history.iloc[-1]

        return {
            "symbol": symbol,
            "open": float(
                latest["Open"]
            ),
            "high": float(
                latest["High"]
            ),
            "low": float(
                latest["Low"]
            ),
            "close": float(
                latest["Close"]
            ),
            "volume": int(
                latest["Volume"]
            ),
            "timestamp": datetime.now(
                timezone.utc
            ),
        }

    async def get_latest_price(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        clean_symbol = (
            symbol.strip().upper()
        )

        if not clean_symbol:
            raise ValueError(
                "Symbol cannot be empty."
            )

        return await run_sync_with_retry(
            lambda: self._fetch_latest_price(
                clean_symbol
            ),
            provider_name=self.provider_name,
            operation_name=(
                f"latest market price for "
                f"{clean_symbol}"
            ),
        )