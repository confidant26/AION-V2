from abc import ABC, abstractmethod


class FinancialDataProvider(ABC):
    provider_name: str

    @abstractmethod
    async def get_income_statements(
        self,
        symbol: str,
    ) -> list[dict]:
        raise NotImplementedError