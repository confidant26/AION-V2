from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BalanceSheetBase(BaseModel):
    period_end_date: date
    period_type: str
    currency: str | None = None

    total_assets: Decimal | None = None
    current_assets: Decimal | None = None
    cash_and_cash_equivalents: Decimal | None = None
    inventory: Decimal | None = None
    accounts_receivable: Decimal | None = None
    total_non_current_assets: Decimal | None = None
    property_plant_equipment: Decimal | None = None
    goodwill: Decimal | None = None
    intangible_assets: Decimal | None = None

    total_liabilities: Decimal | None = None
    current_liabilities: Decimal | None = None
    accounts_payable: Decimal | None = None
    short_term_debt: Decimal | None = None
    total_non_current_liabilities: Decimal | None = None
    long_term_debt: Decimal | None = None
    total_debt: Decimal | None = None

    stockholders_equity: Decimal | None = None
    retained_earnings: Decimal | None = None


class BalanceSheetCreate(BalanceSheetBase):
    asset_id: int


class BalanceSheetResponse(BalanceSheetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int