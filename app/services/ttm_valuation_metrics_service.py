from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
from app.repositories.company_profile_repository import (
    CompanyProfileRepository,
)
from app.schemas.ttm_valuation_metrics import (
    TTMValuationMetricsResponse,
)
from app.services.ttm_financials_service import (
    TTMFinancialsService,
)


class TTMValuationMetricsService:
    def __init__(
        self,
        db: Session,
    ):
        self.asset_repository = AssetRepository(db)
        self.company_profile_repository = (
            CompanyProfileRepository(db)
        )
        self.ttm_financials_service = (
            TTMFinancialsService(db)
        )

    def get_ttm_valuation_metrics(
        self,
        symbol: str,
    ) -> TTMValuationMetricsResponse:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        company_profile = (
            self.company_profile_repository.get_by_asset_id(
                asset.id
            )
        )

        if company_profile is None:
            raise ValueError(
                f"Company profile not found for symbol: "
                f"{clean_symbol}"
            )

        ttm_financials = (
            self.ttm_financials_service.get_ttm_financials(
                clean_symbol
            )
        )

        missing_fields = list(
            ttm_financials.missing_fields
        )

        market_cap = self._decimal_or_none(
            company_profile.market_cap,
            "market_cap",
            missing_fields,
        )

        enterprise_value = self._calculate_enterprise_value(
            market_cap=market_cap,
            total_debt=ttm_financials.total_debt,
            cash_and_cash_equivalents=(
                ttm_financials.cash_and_cash_equivalents
            ),
        )

        price_to_earnings = self._safe_divide(
            market_cap,
            ttm_financials.net_income,
        )

        price_to_sales = self._safe_divide(
            market_cap,
            ttm_financials.total_revenue,
        )

        price_to_book = self._safe_divide(
            market_cap,
            ttm_financials.stockholders_equity,
        )

        ev_to_ebitda = self._safe_divide(
            enterprise_value,
            ttm_financials.ebitda,
        )

        free_cash_flow_yield = self._safe_divide(
            ttm_financials.free_cash_flow,
            market_cap,
        )

        earnings_yield = self._safe_divide(
            ttm_financials.net_income,
            market_cap,
        )

        confidence = self._calculate_confidence(
            missing_fields=missing_fields,
            total_fields=11,
        )

        return TTMValuationMetricsResponse(
            symbol=clean_symbol,
            period_end_date=ttm_financials.period_end_date,
            period_type="ttm",
            currency=(
                company_profile.currency
                or ttm_financials.currency
            ),
            market_cap=market_cap,
            enterprise_value=enterprise_value,
            price_to_earnings=price_to_earnings,
            price_to_sales=price_to_sales,
            price_to_book=price_to_book,
            ev_to_ebitda=ev_to_ebitda,
            free_cash_flow_yield=free_cash_flow_yield,
            earnings_yield=earnings_yield,
            company_profile_id=company_profile.id,
            income_statement_ids=(
                ttm_financials.income_statement_ids
            ),
            balance_sheet_id=(
                ttm_financials.balance_sheet_id
            ),
            cash_flow_statement_ids=(
                ttm_financials.cash_flow_statement_ids
            ),
            quarter_end_dates=(
                ttm_financials.quarter_end_dates
            ),
            missing_fields=missing_fields,
            confidence=confidence,
        )

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
        except (ValueError, TypeError):
            missing_fields.append(field_name)
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