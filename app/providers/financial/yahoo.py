import math
from datetime import date, datetime

import pandas as pd
import yfinance as yf

from app.providers.financial.base import FinancialDataProvider
from app.providers.resilience import run_sync_with_retry


class YahooFinancialProvider(FinancialDataProvider):
    provider_name = "yahoo"

    def _fetch_income_statements(
        self,
        symbol: str,
    ) -> list[dict]:
        ticker = yf.Ticker(
            symbol
        )

        currency = (
            ticker.info.get(
                "currency"
            )
        )

        annual_statements = (
            self._map_income_statement_table(
                table=ticker.income_stmt,
                period_type="annual",
                currency=currency,
            )
        )

        quarterly_statements = (
            self._map_income_statement_table(
                table=(
                    ticker.quarterly_income_stmt
                ),
                period_type="quarterly",
                currency=currency,
            )
        )

        return (
            annual_statements
            + quarterly_statements
        )

    async def get_income_statements(
        self,
        symbol: str,
    ) -> list[dict]:
        clean_symbol = (
            symbol.strip().upper()
        )

        if not clean_symbol:
            raise ValueError(
                "Symbol cannot be empty."
            )

        return await run_sync_with_retry(
            lambda: (
                self._fetch_income_statements(
                    clean_symbol
                )
            ),
            provider_name="Yahoo Finance",
            operation_name=(
                f"income statements for "
                f"{clean_symbol}"
            ),
        )

    def _map_income_statement_table(
        self,
        table: pd.DataFrame | None,
        period_type: str,
        currency: str | None,
    ) -> list[dict]:
        if (
            table is None
            or table.empty
        ):
            return []

        statements: list[dict] = []

        for column in table.columns:
            period_end_date = (
                self._to_date(
                    column
                )
            )

            if period_end_date is None:
                continue

            row = table[column]

            statement = {
                "period_end_date": (
                    period_end_date
                ),
                "period_type": period_type,
                "currency": currency,
                "total_revenue": (
                    self._to_number_or_none(
                        row.get(
                            "Total Revenue"
                        )
                    )
                ),
                "cost_of_revenue": (
                    self._to_number_or_none(
                        row.get(
                            "Cost Of Revenue"
                        )
                    )
                ),
                "gross_profit": (
                    self._to_number_or_none(
                        row.get(
                            "Gross Profit"
                        )
                    )
                ),
                "operating_expense": (
                    self._to_number_or_none(
                        row.get(
                            "Operating Expense"
                        )
                    )
                ),
                "operating_income": (
                    self._to_number_or_none(
                        row.get(
                            "Operating Income"
                        )
                    )
                ),
                "net_non_operating_interest_income_expense": (
                    self._to_number_or_none(
                        row.get(
                            "Net Non Operating Interest "
                            "Income Expense"
                        )
                    )
                ),
                "pretax_income": (
                    self._to_number_or_none(
                        row.get(
                            "Pretax Income"
                        )
                    )
                ),
                "tax_provision": (
                    self._to_number_or_none(
                        row.get(
                            "Tax Provision"
                        )
                    )
                ),
                "net_income": (
                    self._to_number_or_none(
                        row.get(
                            "Net Income"
                        )
                    )
                ),
                "diluted_average_shares": (
                    self._to_number_or_none(
                        row.get(
                            "Diluted Average Shares"
                        )
                    )
                ),
                "diluted_eps": (
                    self._to_string_or_none(
                        row.get(
                            "Diluted EPS"
                        )
                    )
                ),
            }

            if not self._has_core_financial_data(
                statement
            ):
                continue

            statements.append(
                statement
            )

        return statements

    @staticmethod
    def _has_core_financial_data(
        statement: dict,
    ) -> bool:
        core_fields = (
            "total_revenue",
            "gross_profit",
            "operating_income",
            "pretax_income",
            "net_income",
        )

        return any(
            statement.get(
                field_name
            )
            is not None
            for field_name in core_fields
        )

    @staticmethod
    def _to_date(
        value,
    ) -> date | None:
        if isinstance(
            value,
            pd.Timestamp,
        ):
            return value.date()

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        try:
            return pd.to_datetime(
                value
            ).date()

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _to_number_or_none(
        value,
    ):
        if value is None:
            return None

        try:
            numeric_value = float(
                value
            )

            if math.isnan(
                numeric_value
            ):
                return None

            return value

        except (
            TypeError,
            ValueError,
        ):
            return value

    @staticmethod
    def _to_string_or_none(
        value,
    ) -> str | None:
        if value is None:
            return None

        try:
            numeric_value = float(
                value
            )

            if math.isnan(
                numeric_value
            ):
                return None

        except (
            TypeError,
            ValueError,
        ):
            pass

        return str(
            value
        )