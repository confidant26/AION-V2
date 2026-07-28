from abc import ABC, abstractmethod
from typing import Any


class MarketDataProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Veri sağlayıcısının adını döndürür."""
        raise NotImplementedError

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> dict[str, Any]:
        """Bir varlığın en güncel piyasa verisini döndürür."""
        raise NotImplementedError