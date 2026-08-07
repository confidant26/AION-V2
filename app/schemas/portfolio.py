from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="USD", min_length=3, max_length=16)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Portfolio name cannot be empty.")
        return value

    @field_validator("base_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class PortfolioPositionUpsert(BaseModel):
    quantity: Decimal = Field(gt=Decimal("0"))
    average_cost: Decimal = Field(ge=Decimal("0"))
    currency: str | None = Field(default=None, min_length=3, max_length=16)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class PortfolioSummaryResponse(BaseModel):
    id: int
    name: str
    base_currency: str
    created_at: datetime
    updated_at: datetime


class PortfolioPositionResponse(BaseModel):
    id: int
    asset_id: int
    symbol: str
    name: str
    quantity: Decimal
    average_cost: Decimal
    currency: str | None
    latest_price: Decimal | None = None
    cost_basis: Decimal
    market_value: Decimal | None = None
    unrealized_profit_loss: Decimal | None = None
    unrealized_profit_loss_percent: Decimal | None = None


class PortfolioDetailResponse(PortfolioSummaryResponse):
    position_count: int
    total_cost_basis: Decimal
    total_market_value: Decimal | None
    total_unrealized_profit_loss: Decimal | None
    positions: list[PortfolioPositionResponse]


class PortfolioDeleteResponse(BaseModel):
    message: str
    portfolio_id: int


class PositionDeleteResponse(BaseModel):
    message: str
    symbol: str
