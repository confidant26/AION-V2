from app.core.config import settings
from app.providers.financial.base import (
    FinancialDataProvider,
)
from app.providers.financial.fallback import (
    FallbackFinancialProvider,
)
from app.providers.financial.yahoo import (
    YahooFinancialProvider,
)


def create_financial_provider(
    provider_name: str,
) -> FinancialDataProvider:
    clean_name = (
        provider_name
        .strip()
        .lower()
    )

    if clean_name == "yahoo":
        return YahooFinancialProvider()

    raise ValueError(
        f"Unsupported financial data provider: "
        f"{provider_name}"
    )


def get_financial_data_provider(
    provider_name: str | None = None,
) -> FinancialDataProvider:
    if provider_name is not None:
        return create_financial_provider(
            provider_name
        )

    provider_names = (
        settings
        .get_financial_provider_names()
    )

    providers = [
        create_financial_provider(
            name
        )
        for name in provider_names
    ]

    if len(providers) == 1:
        return providers[0]

    return FallbackFinancialProvider(
        providers
    )