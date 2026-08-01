from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CashFlowStatementCreate(BaseModel):
    asset_id: int
    period_end_date: date
    period_type: str
    currency: str | None = None

    operating_cash_flow: Decimal | None = None
    investing_cash_flow: Decimal | None = None
    financing_cash_flow: Decimal | None = None
    capital_expenditure: Decimal | None = None
    free_cash_flow: Decimal | None = None
    depreciation_and_amortization: Decimal | None = None
    stock_based_compensation: Decimal | None = None
    change_in_working_capital: Decimal | None = None
    dividends_paid: Decimal | None = None
    share_repurchases: Decimal | None = None
    debt_issuance: Decimal | None = None
    debt_repayment: Decimal | None = None
    net_change_in_cash: Decimal | None = None


class CashFlowStatementResponse(CashFlowStatementCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int