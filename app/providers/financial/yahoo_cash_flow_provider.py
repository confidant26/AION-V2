from collections.abc import Sequence

import yfinance as yf

from app.mappers.cash_flow_statement_mapper import (
    CashFlowStatementMapper,
)
from app.schemas.cash_flow_statement import (
    CashFlowStatementCreate,
)


class YahooCashFlowProvider:
    @staticmethod
    def _has_financial_data(
        statement: CashFlowStatementCreate,
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
    ) -> list[CashFlowStatementCreate]:
        ticker = yf.Ticker(symbol)

        if period_type == "annual":
            dataframe = ticker.cash_flow
        else:
            dataframe = ticker.quarterly_cash_flow

        if dataframe is None or dataframe.empty:
            return []

        statements: list[
            CashFlowStatementCreate
        ] = []

        for column in dataframe.columns:
            period_end_date = column.date()

            values = dataframe[
                column
            ].to_dict()

            statement = (
                CashFlowStatementMapper
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
    ) -> Sequence[CashFlowStatementCreate]:
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