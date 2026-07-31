import math
from datetime import date, datetime

import pandas as pd
import yfinance as yf

from app.providers.financial.base import FinancialDataProvider


class YahooFinancialProvider(FinancialDataProvider):
    provider_name = "yahoo"

    async def get_income_statements(
        self,
        symbol: str,
    ) -> list[dict]:
        ticker = yf.Ticker(symbol)

        currency = ticker.info.get("currency")

        annual_statements = self._map_income_statement_table(
            table=ticker.income_stmt,
            period_type="annual",
            currency=currency,
        )

        quarterly_statements = self._map_income_statement_table(
            table=ticker.quarterly_income_stmt,
            period_type="quarterly",
            currency=currency,
        )

        return annual_statements + quarterly_statements

    def _map_income_statement_table(
        self,
        table: pd.DataFrame | None,
        period_type: str,
        currency: str | None,
    ) -> list[dict]:
        if table is None:
            return []

        if table.empty:
            return []

        statements: list[dict] = []

        for column in table.columns:
            period_end_date = self._to_date(column)

            if period_end_date is None:
                continue

            row = table[column]

            statements.append(
                {
                    "period_end_date": period_end_date,
                    "period_type": period_type,
                    "currency": currency,
                    "total_revenue": row.get("Total Revenue"),
                    "cost_of_revenue": row.get("Cost Of Revenue"),
                    "gross_profit": row.get("Gross Profit"),
                    "operating_expense": row.get(
                        "Operating Expense"
                    ),
                    "operating_income": row.get(
                        "Operating Income"
                    ),
                    "net_non_operating_interest_income_expense": (
                        row.get(
                            "Net Non Operating Interest "
                            "Income Expense"
                        )
                    ),
                    "pretax_income": row.get("Pretax Income"),
                    "tax_provision": row.get("Tax Provision"),
                    "net_income": row.get("Net Income"),
                    "diluted_average_shares": row.get(
                        "Diluted Average Shares"
                    ),
                    "diluted_eps": self._to_string_or_none(
                        row.get("Diluted EPS")
                    ),
                }
            )

        return statements

    @staticmethod
    def _to_date(
        value,
    ) -> date | None:
        if isinstance(value, pd.Timestamp):
            return value.date()

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        try:
            return pd.to_datetime(value).date()

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_string_or_none(
        value,
    ) -> str | None:
        if value is None:
            return None

        try:
            numeric_value = float(value)

            if math.isnan(numeric_value):
                return None

        except (TypeError, ValueError):
            pass

        return str(value)