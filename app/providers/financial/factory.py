from app.providers.financial.base import FinancialDataProvider
from app.providers.financial.yahoo import YahooFinancialProvider


def get_financial_data_provider(
    provider_name: str = "yahoo",
) -> FinancialDataProvider:
    clean_provider_name = provider_name.strip().lower()

    if clean_provider_name == "yahoo":
        return YahooFinancialProvider()

    raise ValueError(
        f"Unsupported financial data provider: {provider_name}"
    )