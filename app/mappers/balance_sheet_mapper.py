from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.schemas.balance_sheet import BalanceSheetCreate


class BalanceSheetMapper:
    FIELD_MAP = {
        "Total Assets": "total_assets",
        "Current Assets": "current_assets",
        "Cash Cash Equivalents And Short Term Investments": (
            "cash_and_cash_equivalents"
        ),
        "Cash And Cash Equivalents": "cash_and_cash_equivalents",
        "Inventory": "inventory",
        "Accounts Receivable": "accounts_receivable",
        "Total Non Current Assets": "total_non_current_assets",
        "Net PPE": "property_plant_equipment",
        "Gross PPE": "property_plant_equipment",
        "Goodwill": "goodwill",
        "Other Intangible Assets": "intangible_assets",
        "Total Liabilities Net Minority Interest": "total_liabilities",
        "Current Liabilities": "current_liabilities",
        "Payables And Accrued Expenses": "accounts_payable",
        "Accounts Payable": "accounts_payable",
        "Current Debt": "short_term_debt",
        "Current Debt And Capital Lease Obligation": "short_term_debt",
        "Total Non Current Liabilities Net Minority Interest": (
            "total_non_current_liabilities"
        ),
        "Long Term Debt": "long_term_debt",
        "Long Term Debt And Capital Lease Obligation": "long_term_debt",
        "Total Debt": "total_debt",
        "Stockholders Equity": "stockholders_equity",
        "Retained Earnings": "retained_earnings",
    }

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None

        try:
            if hasattr(value, "item"):
                value = value.item()

            if value != value:
                return None

            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

    @classmethod
    def from_yahoo_column(
        cls,
        *,
        asset_id: int,
        period_end_date: date,
        period_type: str,
        currency: str | None,
        values: dict[str, Any],
    ) -> BalanceSheetCreate:
        mapped_values: dict[str, Any] = {
            "asset_id": asset_id,
            "period_end_date": period_end_date,
            "period_type": period_type,
            "currency": currency,
        }

        for yahoo_field, schema_field in cls.FIELD_MAP.items():
            if yahoo_field not in values:
                continue

            mapped_value = cls._to_decimal(values[yahoo_field])

            if (
                schema_field not in mapped_values
                or mapped_values[schema_field] is None
            ):
                mapped_values[schema_field] = mapped_value

        return BalanceSheetCreate(**mapped_values)