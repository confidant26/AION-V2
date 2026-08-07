from datetime import datetime

from pydantic import BaseModel, Field


class WatchlistItemResponse(BaseModel):
    id: int
    asset_id: int
    symbol: str
    name: str
    asset_type: str

    exchange: str | None = None
    market: str | None = None
    currency: str | None = None
    country: str | None = None
    sector: str | None = None
    industry: str | None = None

    created_at: datetime


class WatchlistResponse(BaseModel):
    count: int
    results: list[WatchlistItemResponse] = Field(
        default_factory=list,
    )


class WatchlistDeleteResponse(BaseModel):
    message: str
    symbol: str