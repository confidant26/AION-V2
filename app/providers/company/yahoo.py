from typing import Any

import yfinance as yf

from app.providers.company.base import CompanyDataProvider


class YahooCompanyProvider(CompanyDataProvider):
    @property
    def provider_name(self) -> str:
        return "Yahoo Finance"

    async def get_company_profile(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        clean_symbol = symbol.strip().upper()

        ticker = yf.Ticker(clean_symbol)
        info = ticker.info

        company_name = (
            info.get("longName")
            or info.get("shortName")
            or clean_symbol
        )

        return {
            "symbol": clean_symbol,
            "company_name": company_name,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            "market_cap": info.get("marketCap"),
            "full_time_employees": info.get("fullTimeEmployees"),
            "website": info.get("website"),
            "description": info.get("longBusinessSummary"),
        }