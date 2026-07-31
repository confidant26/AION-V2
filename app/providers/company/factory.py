from app.providers.company.base import CompanyDataProvider
from app.providers.company.yahoo import YahooCompanyProvider


def get_company_data_provider(
    provider_name: str = "yahoo",
) -> CompanyDataProvider:
    clean_provider_name = provider_name.strip().lower()

    if clean_provider_name == "yahoo":
        return YahooCompanyProvider()

    raise ValueError(
        f"Unsupported company data provider: {provider_name}"
    )