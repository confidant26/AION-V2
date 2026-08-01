from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
from app.repositories.ttm_financials_repository import (
    TTMFinancialsRepository,
)
from app.schemas.ttm_financials import TTMFinancialsResponse


class TTMFinancialsService:
    REQUIRED_QUARTERS = 4
    MIN_QUARTER_DAYS = 60
    MAX_QUARTER_DAYS = 120

    def __init__(
        self,
        db: Session,
    ):
        self.asset_repository = AssetRepository(db)
        self.ttm_financials_repository = (
            TTMFinancialsRepository(db)
        )

    def get_ttm_financials(
        self,
        symbol: str,
    ) -> TTMFinancialsResponse:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        matched_quarters = (
            self.ttm_financials_repository
            .get_latest_matched_quarters(
                asset_id=asset.id,
                limit=self.REQUIRED_QUARTERS,
            )
        )

        if len(matched_quarters) != self.REQUIRED_QUARTERS:
            raise ValueError(
                f"Four matched quarterly financial periods "
                f"are required for symbol: {clean_symbol}"
            )

        income_statements = [
            row[0]
            for row in matched_quarters
        ]

        balance_sheets = [
            row[1]
            for row in matched_quarters
        ]

        cash_flow_statements = [
            row[2]
            for row in matched_quarters
        ]

        self._validate_quarter_sequence(
            income_statements=income_statements,
            symbol=clean_symbol,
        )

        latest_income_statement = income_statements[0]
        latest_balance_sheet = balance_sheets[0]

        missing_fields: list[str] = []

        total_revenue = self._sum_field(
            records=income_statements,
            field_name="total_revenue",
            missing_fields=missing_fields,
        )

        operating_income = self._sum_field(
            records=income_statements,
            field_name="operating_income",
            missing_fields=missing_fields,
        )

        net_income = self._sum_field(
            records=income_statements,
            field_name="net_income",
            missing_fields=missing_fields,
        )

        operating_cash_flow = self._sum_field(
            records=cash_flow_statements,
            field_name="operating_cash_flow",
            missing_fields=missing_fields,
        )

        capital_expenditure = self._sum_field(
            records=cash_flow_statements,
            field_name="capital_expenditure",
            missing_fields=missing_fields,
        )

        free_cash_flow = self._sum_field(
            records=cash_flow_statements,
            field_name="free_cash_flow",
            missing_fields=missing_fields,
        )

        depreciation_and_amortization = self._sum_field(
            records=cash_flow_statements,
            field_name="depreciation_and_amortization",
            missing_fields=missing_fields,
        )

        ebitda = self._calculate_ebitda(
            operating_income=operating_income,
            depreciation_and_amortization=(
                depreciation_and_amortization
            ),
        )

        cash_and_cash_equivalents = self._decimal_or_none(
            latest_balance_sheet.cash_and_cash_equivalents,
            "cash_and_cash_equivalents",
            missing_fields,
        )

        total_debt = self._resolve_total_debt(
            balance_sheet=latest_balance_sheet,
            missing_fields=missing_fields,
        )

        stockholders_equity = self._decimal_or_none(
            latest_balance_sheet.stockholders_equity,
            "stockholders_equity",
            missing_fields,
        )

        confidence = self._calculate_confidence(
            missing_fields=missing_fields,
            total_fields=10,
        )

        return TTMFinancialsResponse(
            symbol=clean_symbol,
            period_end_date=(
                latest_income_statement.period_end_date
            ),
            currency=(
                latest_income_statement.currency
                or latest_balance_sheet.currency
            ),
            total_revenue=total_revenue,
            operating_income=operating_income,
            net_income=net_income,
            operating_cash_flow=operating_cash_flow,
            capital_expenditure=capital_expenditure,
            free_cash_flow=free_cash_flow,
            depreciation_and_amortization=(
                depreciation_and_amortization
            ),
            ebitda=ebitda,
            cash_and_cash_equivalents=(
                cash_and_cash_equivalents
            ),
            total_debt=total_debt,
            stockholders_equity=stockholders_equity,
            quarter_end_dates=[
                statement.period_end_date
                for statement in income_statements
            ],
            income_statement_ids=[
                statement.id
                for statement in income_statements
            ],
            cash_flow_statement_ids=[
                statement.id
                for statement in cash_flow_statements
            ],
            balance_sheet_id=latest_balance_sheet.id,
            missing_fields=missing_fields,
            confidence=confidence,
        )

    def _validate_quarter_sequence(
        self,
        *,
        income_statements: list,
        symbol: str,
    ) -> None:
        period_end_dates = [
            statement.period_end_date
            for statement in income_statements
        ]

        if len(set(period_end_dates)) != self.REQUIRED_QUARTERS:
            raise ValueError(
                f"Quarterly financial periods are not unique "
                f"for symbol: {symbol}"
            )

        for index in range(
            len(period_end_dates) - 1
        ):
            newer_date = period_end_dates[index]
            older_date = period_end_dates[index + 1]

            day_difference = (
                newer_date - older_date
            ).days

            if not (
                self.MIN_QUARTER_DAYS
                <= day_difference
                <= self.MAX_QUARTER_DAYS
            ):
                raise ValueError(
                    f"Quarterly financial periods are not "
                    f"consecutive for symbol: {symbol}"
                )

    def _resolve_total_debt(
        self,
        *,
        balance_sheet,
        missing_fields: list[str],
    ) -> Decimal | None:
        if balance_sheet.total_debt is not None:
            return self._decimal_or_none(
                balance_sheet.total_debt,
                "total_debt",
                missing_fields,
            )

        short_term_debt = self._decimal_without_tracking(
            balance_sheet.short_term_debt
        )

        long_term_debt = self._decimal_without_tracking(
            balance_sheet.long_term_debt
        )

        if (
            short_term_debt is not None
            and long_term_debt is not None
        ):
            return short_term_debt + long_term_debt

        missing_fields.append("total_debt")
        return None

    @staticmethod
    def _sum_field(
        *,
        records: list,
        field_name: str,
        missing_fields: list[str],
    ) -> Decimal | None:
        values: list[Decimal] = []

        for record in records:
            value = getattr(
                record,
                field_name,
                None,
            )

            if value is None:
                missing_fields.append(field_name)
                return None

            try:
                values.append(
                    Decimal(str(value))
                )
            except (
                InvalidOperation,
                ValueError,
                TypeError,
            ):
                missing_fields.append(field_name)
                return None

        return sum(
            values,
            Decimal("0"),
        )

    @staticmethod
    def _calculate_ebitda(
        *,
        operating_income: Decimal | None,
        depreciation_and_amortization: Decimal | None,
    ) -> Decimal | None:
        if (
            operating_income is None
            or depreciation_and_amortization is None
        ):
            return None

        return (
            operating_income
            + depreciation_and_amortization
        )

    @staticmethod
    def _decimal_or_none(
        value,
        field_name: str,
        missing_fields: list[str],
    ) -> Decimal | None:
        if value is None:
            missing_fields.append(field_name)
            return None

        try:
            return Decimal(str(value))
        except (
            InvalidOperation,
            ValueError,
            TypeError,
        ):
            missing_fields.append(field_name)
            return None

    @staticmethod
    def _decimal_without_tracking(
        value,
    ) -> Decimal | None:
        if value is None:
            return None

        try:
            return Decimal(str(value))
        except (
            InvalidOperation,
            ValueError,
            TypeError,
        ):
            return None

    @staticmethod
    def _calculate_confidence(
        *,
        missing_fields: list[str],
        total_fields: int,
    ) -> Decimal:
        available_fields = (
            total_fields
            - len(set(missing_fields))
        )

        if available_fields < 0:
            available_fields = 0

        return (
            Decimal(available_fields)
            / Decimal(total_fields)
        )