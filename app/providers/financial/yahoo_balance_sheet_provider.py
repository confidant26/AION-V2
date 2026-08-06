from collections.abc import Sequence

import yfinance as yf

from app.mappers.balance_sheet_mapper import BalanceSheetMapper
from app.schemas.balance_sheet import BalanceSheetCreate


class YahooBalanceSheetProvider:
    @staticmethod
    def _has_financial_data(
        statement: BalanceSheetCreate,
    ) -> bool:
        values = statement.model_dump(
            exclude={
                "asset_id",
                "period_end_date",
                "period_type",
                "currency",
            }
        )

        return any(
            value is not None
            for value in values.values()
        )

    @classmethod
    def _extract_statements(
        cls,
        *,
        asset_id: int,
        symbol: str,
        period_type: str,
        currency: str | None,
    ) -> list[BalanceSheetCreate]:
        ticker = yf.Ticker(symbol)

        if period_type == "annual":
            dataframe = ticker.balance_sheet
        else:
            dataframe = ticker.quarterly_balance_sheet

        if dataframe is None or dataframe.empty:
            return []

        statements: list[BalanceSheetCreate] = []

        for column in dataframe.columns:
            period_end_date = column.date()

            values = dataframe[
                column
            ].to_dict()

            statement = (
                BalanceSheetMapper
                .from_yahoo_column(
                    asset_id=asset_id,
                    period_end_date=period_end_date,
                    period_type=period_type,
                    currency=currency,
                    values=values,
                )
            )

            if not cls._has_financial_data(
                statement
            ):
                continue

            statements.append(
                statement
            )

        return statements

    @classmethod
    def fetch(
        cls,
        *,
        asset_id: int,
        symbol: str,
        currency: str | None,
    ) -> Sequence[BalanceSheetCreate]:
        annual_statements = (
            cls._extract_statements(
                asset_id=asset_id,
                symbol=symbol,
                period_type="annual",
                currency=currency,
            )
        )

        quarterly_statements = (
            cls._extract_statements(
                asset_id=asset_id,
                symbol=symbol,
                period_type="quarterly",
                currency=currency,
            )
        )

        return [
            *annual_statements,
            *quarterly_statements,
        ]