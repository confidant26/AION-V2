from app.providers.fallback import (
    execute_with_fallback,
)
from app.providers.financial.base import (
    FinancialDataProvider,
)


class FallbackFinancialProvider(
    FinancialDataProvider
):
    def __init__(
        self,
        providers: list[
            FinancialDataProvider
        ],
    ) -> None:
        if not providers:
            raise ValueError(
                "At least one financial provider "
                "is required."
            )

        self.providers = providers

        names = [
            provider.provider_name
            for provider in providers
        ]

        self.provider_name = (
            "Fallback Financial Provider "
            f"({', '.join(names)})"
        )

    async def get_income_statements(
        self,
        symbol: str,
    ) -> list[dict]:
        return await execute_with_fallback(
            providers=self.providers,
            operation=lambda provider: (
                provider.get_income_statements(
                    symbol
                )
            ),
            operation_name=(
                f"income statements for "
                f"{symbol.strip().upper()}"
            ),
        )