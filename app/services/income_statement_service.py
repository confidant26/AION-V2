import math

from sqlalchemy.orm import Session

from app.mappers.income_statement import (
    map_income_statement_create_to_model,
)
from app.providers.financial.base import FinancialDataProvider
from app.repositories.asset_repository import AssetRepository
from app.repositories.income_statement_repository import (
    IncomeStatementRepository,
)
from app.schemas.income_statement import IncomeStatementCreate


class IncomeStatementService:
    def __init__(
        self,
        db: Session,
        provider: FinancialDataProvider,
    ):
        self.asset_repository = AssetRepository(db)
        self.income_statement_repository = (
            IncomeStatementRepository(db)
        )
        self.provider = provider

    async def collect_income_statements(
        self,
        symbol: str,
    ) -> list:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(clean_symbol)

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        raw_statements = (
            await self.provider.get_income_statements(
                clean_symbol
            )
        )

        if not raw_statements:
            raise ValueError(
                f"Income statements not found for symbol: "
                f"{clean_symbol}"
            )

        saved_statements = []

        for raw_statement in raw_statements:
            statement_data = IncomeStatementCreate(
                period_end_date=raw_statement[
                    "period_end_date"
                ],
                period_type=raw_statement["period_type"],
                currency=raw_statement.get("currency"),
                total_revenue=self._to_int_or_none(
                    raw_statement.get("total_revenue")
                ),
                cost_of_revenue=self._to_int_or_none(
                    raw_statement.get("cost_of_revenue")
                ),
                gross_profit=self._to_int_or_none(
                    raw_statement.get("gross_profit")
                ),
                operating_expense=self._to_int_or_none(
                    raw_statement.get("operating_expense")
                ),
                operating_income=self._to_int_or_none(
                    raw_statement.get("operating_income")
                ),
                net_non_operating_interest_income_expense=(
                    self._to_int_or_none(
                        raw_statement.get(
                            "net_non_operating_interest_income_expense"
                        )
                    )
                ),
                pretax_income=self._to_int_or_none(
                    raw_statement.get("pretax_income")
                ),
                tax_provision=self._to_int_or_none(
                    raw_statement.get("tax_provision")
                ),
                net_income=self._to_int_or_none(
                    raw_statement.get("net_income")
                ),
                diluted_average_shares=self._to_int_or_none(
                    raw_statement.get(
                        "diluted_average_shares"
                    )
                ),
                diluted_eps=self._to_string_or_none(
                    raw_statement.get("diluted_eps")
                ),
            )

            existing_statement = (
                self.income_statement_repository
                .get_by_asset_and_period(
                    asset_id=asset.id,
                    period_end_date=(
                        statement_data.period_end_date
                    ),
                    period_type=statement_data.period_type,
                )
            )

            if existing_statement is None:
                income_statement = (
                    map_income_statement_create_to_model(
                        data=statement_data,
                        asset_id=asset.id,
                    )
                )

                saved_statement = (
                    self.income_statement_repository.create(
                        income_statement
                    )
                )

                saved_statements.append(saved_statement)
                continue

            existing_statement.currency = (
                statement_data.currency
            )
            existing_statement.total_revenue = (
                statement_data.total_revenue
            )
            existing_statement.cost_of_revenue = (
                statement_data.cost_of_revenue
            )
            existing_statement.gross_profit = (
                statement_data.gross_profit
            )
            existing_statement.operating_expense = (
                statement_data.operating_expense
            )
            existing_statement.operating_income = (
                statement_data.operating_income
            )
            existing_statement.net_non_operating_interest_income_expense = (
                statement_data
                .net_non_operating_interest_income_expense
            )
            existing_statement.pretax_income = (
                statement_data.pretax_income
            )
            existing_statement.tax_provision = (
                statement_data.tax_provision
            )
            existing_statement.net_income = (
                statement_data.net_income
            )
            existing_statement.diluted_average_shares = (
                statement_data.diluted_average_shares
            )
            existing_statement.diluted_eps = (
                statement_data.diluted_eps
            )

            saved_statement = (
                self.income_statement_repository.update(
                    existing_statement
                )
            )

            saved_statements.append(saved_statement)

        return saved_statements

    def get_income_statements(
        self,
        symbol: str,
        limit: int = 20,
    ) -> list:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(clean_symbol)

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        statements = (
            self.income_statement_repository.get_by_asset_id(
                asset_id=asset.id,
                limit=limit,
            )
        )

        if not statements:
            raise ValueError(
                f"Income statements not found for symbol: "
                f"{clean_symbol}"
            )

        return statements

    @staticmethod
    def _to_int_or_none(
        value,
    ) -> int | None:
        if value is None:
            return None

        try:
            numeric_value = float(value)

            if math.isnan(numeric_value):
                return None

            return int(numeric_value)

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_string_or_none(
        value,
    ) -> str | None:
        if value is None:
            return None

        value_as_string = str(value)

        if value_as_string.lower() == "nan":
            return None

        return value_as_string