from datetime import date, datetime

from pydantic import BaseModel, Field


class FreshnessComponentResponse(BaseModel):
    status: str
    stale: bool
    latest_period_end_date: date | None = None
    latest_timestamp: datetime | None = None
    age_days: int | None = None
    age_minutes: int | None = None
    max_age_days: int | None = None
    max_age_minutes: int | None = None


class AssetFreshnessResponse(BaseModel):
    symbol: str
    status: str
    stale_components: list[str] = Field(
        default_factory=list,
    )
    components: dict[
        str,
        FreshnessComponentResponse,
    ] = Field(
        default_factory=dict,
    )
