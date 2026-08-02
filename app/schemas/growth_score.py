from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GrowthScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_end_date: date
    previous_period_end_date: date
    period_type: str
    currency: str | None = None

    revenue_growth_score: Decimal | None = None
    operating_income_growth_score: Decimal | None = None
    net_income_growth_score: Decimal | None = None
    free_cash_flow_growth_score: Decimal | None = None
    total_assets_growth_score: Decimal | None = None
    stockholders_equity_growth_score: Decimal | None = None

    growth_score: Decimal | None = None

    revenue_growth: Decimal | None = None
    operating_income_growth: Decimal | None = None
    net_income_growth: Decimal | None = None
    free_cash_flow_growth: Decimal | None = None
    total_assets_growth: Decimal | None = None
    stockholders_equity_growth: Decimal | None = None

    current_income_statement_id: int
    previous_income_statement_id: int

    current_balance_sheet_id: int
    previous_balance_sheet_id: int

    current_cash_flow_statement_id: int
    previous_cash_flow_statement_id: int

    missing_fields: list[str] = Field(
        default_factory=list,
    )

    confidence: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
    )