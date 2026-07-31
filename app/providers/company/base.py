from abc import ABC
from abc import abstractmethod
from typing import Any


class CompanyDataProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def get_company_profile(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        pass