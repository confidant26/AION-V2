from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class RankingItem(BaseModel):
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

    as_of_date: date

    growth_score: Decimal | None = None
    quality_score: Decimal | None = None
    valuation_score: Decimal | None = None
    composite_score: Decimal

    confidence: Decimal

    period_alignment_ok: bool
    component_date_spread_days: int | None = None

    missing_components: list[str] = Field(
        default_factory=list,
    )


class RankingResponse(BaseModel):
    total: int
    count: int
    offset: int
    limit: int
    results: list[RankingItem] = Field(
        default_factory=list,
    )


class ScreenerResponse(BaseModel):
    total: int
    count: int
    offset: int
    limit: int
    results: list[RankingItem] = Field(
        default_factory=list,
    )