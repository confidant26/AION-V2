from datetime import datetime
from typing import Any

import yfinance as yf

from app.providers.market.base import MarketDataProvider


class YahooMarketProvider(MarketDataProvider):
    @property
    def provider_name(self) -> str:
        return "Yahoo Finance"

    async def get_latest_price(self, symbol: str) -> dict[str, Any]:
        ticker = yf.Ticker(symbol)

        history = ticker.history(period="1d")

        if history.empty:
            raise ValueError(f"No market data found for {symbol}")

        latest = history.iloc[-1]

        return {
            "symbol": symbol.upper(),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "close": float(latest["Close"]),
            "volume": int(latest["Volume"]),
            "timestamp": datetime.utcnow(),
        }