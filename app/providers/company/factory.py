from app.core.config import settings
from app.providers.company.base import (
    CompanyDataProvider,
)
from app.providers.company.fallback import (
    FallbackCompanyProvider,
)
from app.providers.company.yahoo import (
    YahooCompanyProvider,
)


def create_company_provider(
    provider_name: str,
) -> CompanyDataProvider:
    clean_name = (
        provider_name
        .strip()
        .lower()
    )

    if clean_name == "yahoo":
        return YahooCompanyProvider()

    raise ValueError(
        f"Unsupported company data provider: "
        f"{provider_name}"
    )


def get_company_data_provider(
    provider_name: str | None = None,
) -> CompanyDataProvider:
    if provider_name is not None:
        return create_company_provider(
            provider_name
        )

    provider_names = (
        settings.get_company_provider_names()
    )

    providers = [
        create_company_provider(
            name
        )
        for name in provider_names
    ]

    if len(providers) == 1:
        return providers[0]

    return FallbackCompanyProvider(
        providers
    )