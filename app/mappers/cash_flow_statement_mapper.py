import math
from datetime import date
from decimal import Decimal, InvalidOperation

from app.schemas.cash_flow_statement import CashFlowStatementCreate


class CashFlowStatementMapper:
    @staticmethod
    def _to_decimal(value) -> Decimal | None:
        if value is None:
            return None

        try:
            numeric_value = float(value)

            if math.isnan(numeric_value):
                return None

            return Decimal(str(value))

        except (TypeError, ValueError, InvalidOperation):
            return None

    @classmethod
    def from_yahoo_column(
        cls,
        *,
        asset_id: int,
        period_end_date: date,
        period_type: str,
        currency: str | None,
        values: dict,
    ) -> CashFlowStatementCreate:
        return CashFlowStatementCreate(
            asset_id=asset_id,
            period_end_date=period_end_date,
            period_type=period_type,
            currency=currency,
            operating_cash_flow=cls._to_decimal(
                values.get("Operating Cash Flow")
            ),
            investing_cash_flow=cls._to_decimal(
                values.get("Investing Cash Flow")
            ),
            financing_cash_flow=cls._to_decimal(
                values.get("Financing Cash Flow")
            ),
            capital_expenditure=cls._to_decimal(
                values.get("Capital Expenditure")
            ),
            free_cash_flow=cls._to_decimal(
                values.get("Free Cash Flow")
            ),
            depreciation_and_amortization=cls._to_decimal(
                values.get("Depreciation And Amortization")
            ),
            stock_based_compensation=cls._to_decimal(
                values.get("Stock Based Compensation")
            ),
            change_in_working_capital=cls._to_decimal(
                values.get("Change In Working Capital")
            ),
            dividends_paid=cls._to_decimal(
                values.get("Cash Dividends Paid")
            ),
            share_repurchases=cls._to_decimal(
                values.get("Repurchase Of Capital Stock")
            ),
            debt_issuance=cls._to_decimal(
                values.get("Issuance Of Debt")
            ),
            debt_repayment=cls._to_decimal(
                values.get("Repayment Of Debt")
            ),
            net_change_in_cash=cls._to_decimal(
                values.get("Changes In Cash")
            ),
        )