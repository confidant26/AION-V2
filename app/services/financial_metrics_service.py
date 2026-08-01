from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
from app.repositories.financial_metrics_repository import (
    FinancialMetricsRepository,
)
from app.schemas.financial_metrics import FinancialMetricsResponse


class FinancialMetricsService:
    def __init__(
        self,
        db: Session,
    ):
        self.asset_repository = AssetRepository(db)
        self.financial_metrics_repository = (
            FinancialMetricsRepository(db)
        )

    def get_financial_metrics(
        self,
        symbol: str,
        period_type: str | None = None,
        limit: int = 20,
    ) -> list[FinancialMetricsResponse]:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        matched_periods = (
            self.financial_metrics_repository.get_matched_periods(
                asset_id=asset.id,
                period_type=period_type,
                limit=limit,
            )
        )

        if not matched_periods:
            raise ValueError(
                f"Matched financial statements not found for symbol: "
                f"{clean_symbol}"
            )

        results: list[FinancialMetricsResponse] = []

        for (
            income_statement,
            balance_sheet,
            cash_flow_statement,
        ) in matched_periods:
            missing_fields: list[str] = []

            total_revenue = self._decimal_or_none(
                income_statement.total_revenue,
                "total_revenue",
                missing_fields,
            )

            operating_income = self._decimal_or_none(
                income_statement.operating_income,
                "operating_income",
                missing_fields,
            )

            net_income = self._decimal_or_none(
                income_statement.net_income,
                "net_income",
                missing_fields,
            )

            current_assets = self._decimal_or_none(
                balance_sheet.current_assets,
                "current_assets",
                missing_fields,
            )

            current_liabilities = self._decimal_or_none(
                balance_sheet.current_liabilities,
                "current_liabilities",
                missing_fields,
            )

            total_debt = self._decimal_or_none(
                balance_sheet.total_debt,
                "total_debt",
                missing_fields,
            )

            stockholders_equity = self._decimal_or_none(
                balance_sheet.stockholders_equity,
                "stockholders_equity",
                missing_fields,
            )

            total_assets = self._decimal_or_none(
                balance_sheet.total_assets,
                "total_assets",
                missing_fields,
            )

            free_cash_flow = self._decimal_or_none(
                cash_flow_statement.free_cash_flow,
                "free_cash_flow",
                missing_fields,
            )

            operating_margin = self._safe_divide(
                operating_income,
                total_revenue,
            )

            net_margin = self._safe_divide(
                net_income,
                total_revenue,
            )

            current_ratio = self._safe_divide(
                current_assets,
                current_liabilities,
            )

            debt_to_equity = self._safe_divide(
                total_debt,
                stockholders_equity,
            )

            return_on_assets = self._safe_divide(
                net_income,
                total_assets,
            )

            return_on_equity = self._safe_divide(
                net_income,
                stockholders_equity,
            )

            free_cash_flow_margin = self._safe_divide(
                free_cash_flow,
                total_revenue,
            )

            confidence = self._calculate_confidence(
                missing_fields=missing_fields,
                total_fields=9,
            )

            results.append(
                FinancialMetricsResponse(
                    symbol=clean_symbol,
                    period_end_date=(
                        income_statement.period_end_date
                    ),
                    period_type=(
                        income_statement.period_type
                    ),
                    currency=income_statement.currency,
                    operating_margin=operating_margin,
                    net_margin=net_margin,
                    current_ratio=current_ratio,
                    debt_to_equity=debt_to_equity,
                    return_on_assets=return_on_assets,
                    return_on_equity=return_on_equity,
                    free_cash_flow_margin=(
                        free_cash_flow_margin
                    ),
                    income_statement_id=(
                        income_statement.id
                    ),
                    balance_sheet_id=balance_sheet.id,
                    cash_flow_statement_id=(
                        cash_flow_statement.id
                    ),
                    missing_fields=missing_fields,
                    confidence=confidence,
                )
            )

        return results

    @staticmethod
    def _safe_divide(
        numerator: Decimal | None,
        denominator: Decimal | None,
    ) -> Decimal | None:
        if numerator is None or denominator is None:
            return None

        if denominator == 0:
            return None

        return numerator / denominator

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
        except (InvalidOperation, ValueError, TypeError):
            missing_fields.append(field_name)
            return None

    @staticmethod
    def _calculate_confidence(
        *,
        missing_fields: list[str],
        total_fields: int,
    ) -> Decimal:
        available_fields = total_fields - len(
            set(missing_fields)
        )

        if available_fields < 0:
            available_fields = 0

        return (
            Decimal(available_fields)
            / Decimal(total_fields)
        )