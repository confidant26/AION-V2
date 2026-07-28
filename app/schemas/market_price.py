from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MarketPriceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=20)
    open: float
    high: float
    low: float
    close: float
    volume: int = Field(ge=0)
    timestamp: datetime