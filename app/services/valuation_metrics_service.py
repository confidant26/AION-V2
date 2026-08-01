from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
from app.repositories.valuation_metrics_repository import (
    ValuationMetricsRepository,
)
from app.schemas.valuation_metrics import ValuationMetricsResponse


class ValuationMetricsService:
    def __init__(
        self,
        db: Session,
    ):
        self.asset_repository = AssetRepository(db)
        self.valuation_metrics_repository = (
            ValuationMetricsRepository(db)
        )

    def get_valuation_metrics(
        self,
        symbol: str,
        limit: int = 20,
    ) -> list[ValuationMetricsResponse]:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        company_profile = (
            self.valuation_metrics_repository.get_company_profile(
                asset_id=asset.id,
            )
        )

        if company_profile is None:
            raise ValueError(
                f"Company profile not found for symbol: "
                f"{clean_symbol}"
            )

        matched_periods = (
            self.valuation_metrics_repository.get_matched_periods(
                asset_id=asset.id,
                period_type="annual",
                limit=limit,
            )
        )

        if not matched_periods:
            raise ValueError(
                f"Matched annual financial statements not found "
                f"for symbol: {clean_symbol}"
            )

        results: list[ValuationMetricsResponse] = []

        for (
            income_statement,
            balance_sheet,
            cash_flow_statement,
        ) in matched_periods:
            missing_fields: list[str] = []

            market_cap = self._decimal_or_none(
                company_profile.market_cap,
                "market_cap",
                missing_fields,
            )

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

            stockholders_equity = self._decimal_or_none(
                balance_sheet.stockholders_equity,
                "stockholders_equity",
                missing_fields,
            )

            cash_and_cash_equivalents = self._decimal_or_none(
                balance_sheet.cash_and_cash_equivalents,
                "cash_and_cash_equivalents",
                missing_fields,
            )

            total_debt = self._resolve_total_debt(
                balance_sheet=balance_sheet,
                missing_fields=missing_fields,
            )

            depreciation_and_amortization = (
                self._decimal_or_none(
                    cash_flow_statement.depreciation_and_amortization,
                    "depreciation_and_amortization",
                    missing_fields,
                )
            )

            free_cash_flow = self._decimal_or_none(
                cash_flow_statement.free_cash_flow,
                "free_cash_flow",
                missing_fields,
            )

            enterprise_value = self._calculate_enterprise_value(
                market_cap=market_cap,
                total_debt=total_debt,
                cash_and_cash_equivalents=(
                    cash_and_cash_equivalents
                ),
            )

            ebitda = self._calculate_ebitda(
                operating_income=operating_income,
                depreciation_and_amortization=(
                    depreciation_and_amortization
                ),
            )

            price_to_earnings = self._safe_divide(
                market_cap,
                net_income,
            )

            price_to_sales = self._safe_divide(
                market_cap,
                total_revenue,
            )

            price_to_book = self._safe_divide(
                market_cap,
                stockholders_equity,
            )

            ev_to_ebitda = self._safe_divide(
                enterprise_value,
                ebitda,
            )

            free_cash_flow_yield = self._safe_divide(
                free_cash_flow,
                market_cap,
            )

            earnings_yield = self._safe_divide(
                net_income,
                market_cap,
            )

            confidence = self._calculate_confidence(
                missing_fields=missing_fields,
                total_fields=9,
            )

            results.append(
                ValuationMetricsResponse(
                    symbol=clean_symbol,
                    period_end_date=(
                        income_statement.period_end_date
                    ),
                    period_type=(
                        income_statement.period_type
                    ),
                    currency=(
                        company_profile.currency
                        or income_statement.currency
                    ),
                    market_cap=market_cap,
                    enterprise_value=enterprise_value,
                    price_to_earnings=price_to_earnings,
                    price_to_sales=price_to_sales,
                    price_to_book=price_to_book,
                    ev_to_ebitda=ev_to_ebitda,
                    free_cash_flow_yield=(
                        free_cash_flow_yield
                    ),
                    earnings_yield=earnings_yield,
                    company_profile_id=company_profile.id,
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
    def _calculate_enterprise_value(
        *,
        market_cap: Decimal | None,
        total_debt: Decimal | None,
        cash_and_cash_equivalents: Decimal | None,
    ) -> Decimal | None:
        if (
            market_cap is None
            or total_debt is None
            or cash_and_cash_equivalents is None
        ):
            return None

        return (
            market_cap
            + total_debt
            - cash_and_cash_equivalents
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
    def _decimal_without_tracking(
        value,
    ) -> Decimal | None:
        if value is None:
            return None

        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
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