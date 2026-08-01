from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FinancialMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_end_date: date
    period_type: str
    currency: str | None = None

    operating_margin: Decimal | None = None
    net_margin: Decimal | None = None
    current_ratio: Decimal | None = None
    debt_to_equity: Decimal | None = None
    return_on_assets: Decimal | None = None
    return_on_equity: Decimal | None = None
    free_cash_flow_margin: Decimal | None = None

    income_statement_id: int
    balance_sheet_id: int
    cash_flow_statement_id: int

    missing_fields: list[str] = Field(
        default_factory=list,
    )

    confidence: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1"),
    )