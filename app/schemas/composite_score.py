from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CompositeScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    as_of_date: date
    currency: str | None = None

    growth_score: Decimal | None = None
    quality_score: Decimal | None = None
    valuation_score: Decimal | None = None

    composite_score: Decimal | None = None

    growth_weight: Decimal
    quality_weight: Decimal
    valuation_weight: Decimal

    growth_period_end_date: date | None = None
    quality_period_end_date: date | None = None
    valuation_period_end_date: date | None = None

    oldest_component_date: date | None = None
    newest_component_date: date | None = None
    component_date_spread_days: int | None = None
    period_alignment_ok: bool

    missing_components: list[str] = Field(
        default_factory=list,
    )

    confidence: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
    )