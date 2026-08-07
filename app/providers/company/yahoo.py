from typing import Any

import yfinance as yf

from app.providers.company.base import CompanyDataProvider
from app.providers.resilience import run_sync_with_retry


class YahooCompanyProvider(CompanyDataProvider):
    @property
    def provider_name(self) -> str:
        return "Yahoo Finance"

    @staticmethod
    def _fetch_profile(
        symbol: str,
    ) -> dict[str, Any]:
        ticker = yf.Ticker(
            symbol
        )

        info = ticker.info

        if not info:
            raise ValueError(
                f"No company profile found for {symbol}"
            )

        company_name = (
            info.get("longName")
            or info.get("shortName")
            or symbol
        )

        return {
            "symbol": symbol,
            "company_name": company_name,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            "market_cap": info.get("marketCap"),
            "full_time_employees": (
                info.get("fullTimeEmployees")
            ),
            "website": info.get("website"),
            "description": (
                info.get("longBusinessSummary")
            ),
        }

    async def get_company_profile(
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
            lambda: self._fetch_profile(
                clean_symbol
            ),
            provider_name=self.provider_name,
            operation_name=(
                f"company profile for "
                f"{clean_symbol}"
            ),
        )