from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
from app.repositories.growth_metrics_repository import (
    GrowthMetricsRepository,
)
from app.schemas.growth_metrics import GrowthMetricsResponse


class GrowthMetricsService:
    MIN_ANNUAL_DAYS = 300
    MAX_ANNUAL_DAYS = 430

    def __init__(
        self,
        db: Session,
    ):
        self.asset_repository = AssetRepository(db)
        self.growth_metrics_repository = (
            GrowthMetricsRepository(db)
        )

    def get_growth_metrics(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[GrowthMetricsResponse]:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        matched_periods = (
            self.growth_metrics_repository
            .get_annual_matched_periods(
                asset_id=asset.id,
                limit=limit + 1,
            )
        )

        if len(matched_periods) < 2:
            raise ValueError(
                f"At least two matched annual financial periods "
                f"are required for symbol: {clean_symbol}"
            )

        results: list[GrowthMetricsResponse] = []

        for index in range(
            min(limit, len(matched_periods) - 1)
        ):
            current_period = matched_periods[index]
            previous_period = matched_periods[index + 1]

            current_income = current_period[0]
            current_balance = current_period[1]
            current_cash_flow = current_period[2]

            previous_income = previous_period[0]
            previous_balance = previous_period[1]
            previous_cash_flow = previous_period[2]

            self._validate_annual_sequence(
                current_date=current_income.period_end_date,
                previous_date=previous_income.period_end_date,
                symbol=clean_symbol,
            )

            missing_fields: list[str] = []

            current_revenue = self._decimal_or_none(
                current_income.total_revenue,
                "current_total_revenue",
                missing_fields,
            )
            previous_revenue = self._decimal_or_none(
                previous_income.total_revenue,
                "previous_total_revenue",
                missing_fields,
            )

            current_operating_income = self._decimal_or_none(
                current_income.operating_income,
                "current_operating_income",
                missing_fields,
            )
            previous_operating_income = self._decimal_or_none(
                previous_income.operating_income,
                "previous_operating_income",
                missing_fields,
            )

            current_net_income = self._decimal_or_none(
                current_income.net_income,
                "current_net_income",
                missing_fields,
            )
            previous_net_income = self._decimal_or_none(
                previous_income.net_income,
                "previous_net_income",
                missing_fields,
            )

            current_free_cash_flow = self._decimal_or_none(
                current_cash_flow.free_cash_flow,
                "current_free_cash_flow",
                missing_fields,
            )
            previous_free_cash_flow = self._decimal_or_none(
                previous_cash_flow.free_cash_flow,
                "previous_free_cash_flow",
                missing_fields,
            )

            current_total_assets = self._decimal_or_none(
                current_balance.total_assets,
                "current_total_assets",
                missing_fields,
            )
            previous_total_assets = self._decimal_or_none(
                previous_balance.total_assets,
                "previous_total_assets",
                missing_fields,
            )

            current_equity = self._decimal_or_none(
                current_balance.stockholders_equity,
                "current_stockholders_equity",
                missing_fields,
            )
            previous_equity = self._decimal_or_none(
                previous_balance.stockholders_equity,
                "previous_stockholders_equity",
                missing_fields,
            )

            revenue_growth = self._calculate_growth(
                current=current_revenue,
                previous=previous_revenue,
            )

            operating_income_growth = self._calculate_growth(
                current=current_operating_income,
                previous=previous_operating_income,
            )

            net_income_growth = self._calculate_growth(
                current=current_net_income,
                previous=previous_net_income,
            )

            free_cash_flow_growth = self._calculate_growth(
                current=current_free_cash_flow,
                previous=previous_free_cash_flow,
            )

            total_assets_growth = self._calculate_growth(
                current=current_total_assets,
                previous=previous_total_assets,
            )

            stockholders_equity_growth = (
                self._calculate_growth(
                    current=current_equity,
                    previous=previous_equity,
                )
            )

            confidence = self._calculate_confidence(
                missing_fields=missing_fields,
                total_fields=12,
            )

            results.append(
                GrowthMetricsResponse(
                    symbol=clean_symbol,
                    period_end_date=(
                        current_income.period_end_date
                    ),
                    previous_period_end_date=(
                        previous_income.period_end_date
                    ),
                    period_type="annual",
                    currency=(
                        current_income.currency
                        or current_balance.currency
                    ),
                    revenue_growth=revenue_growth,
                    operating_income_growth=(
                        operating_income_growth
                    ),
                    net_income_growth=net_income_growth,
                    free_cash_flow_growth=(
                        free_cash_flow_growth
                    ),
                    total_assets_growth=(
                        total_assets_growth
                    ),
                    stockholders_equity_growth=(
                        stockholders_equity_growth
                    ),
                    current_income_statement_id=(
                        current_income.id
                    ),
                    previous_income_statement_id=(
                        previous_income.id
                    ),
                    current_balance_sheet_id=(
                        current_balance.id
                    ),
                    previous_balance_sheet_id=(
                        previous_balance.id
                    ),
                    current_cash_flow_statement_id=(
                        current_cash_flow.id
                    ),
                    previous_cash_flow_statement_id=(
                        previous_cash_flow.id
                    ),
                    missing_fields=missing_fields,
                    confidence=confidence,
                )
            )

        return results

    def _validate_annual_sequence(
        self,
        *,
        current_date,
        previous_date,
        symbol: str,
    ) -> None:
        day_difference = (
            current_date - previous_date
        ).days

        if not (
            self.MIN_ANNUAL_DAYS
            <= day_difference
            <= self.MAX_ANNUAL_DAYS
        ):
            raise ValueError(
                f"Annual financial periods are not consecutive "
                f"for symbol: {symbol}"
            )

    @staticmethod
    def _calculate_growth(
        *,
        current: Decimal | None,
        previous: Decimal | None,
    ) -> Decimal | None:
        if current is None or previous is None:
            return None

        if previous == 0:
            return None

        return (
            current - previous
        ) / abs(previous)

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