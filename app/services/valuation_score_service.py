from decimal import Decimal

from sqlalchemy.orm import Session

from app.schemas.valuation_score import ValuationScoreResponse
from app.services.ttm_valuation_metrics_service import (
    TTMValuationMetricsService,
)


class ValuationScoreService:
    SCORE_COMPONENT_COUNT = 2

    def __init__(
        self,
        db: Session,
    ):
        self.ttm_valuation_metrics_service = (
            TTMValuationMetricsService(db)
        )

    def get_valuation_score(
        self,
        symbol: str,
    ) -> ValuationScoreResponse:
        valuation_metrics = (
            self.ttm_valuation_metrics_service
            .get_ttm_valuation_metrics(
                symbol=symbol,
            )
        )

        earnings_yield_score = (
            self._score_earnings_yield(
                valuation_metrics.earnings_yield
            )
        )

        free_cash_flow_yield_score = (
            self._score_free_cash_flow_yield(
                valuation_metrics.free_cash_flow_yield
            )
        )

        valuation_score = self._average_scores(
            [
                earnings_yield_score,
                free_cash_flow_yield_score,
            ]
        )

        score_coverage = self._calculate_score_coverage(
            [
                earnings_yield_score,
                free_cash_flow_yield_score,
            ]
        )

        confidence = min(
            valuation_metrics.confidence,
            score_coverage,
        )

        return ValuationScoreResponse(
            symbol=valuation_metrics.symbol,
            period_end_date=(
                valuation_metrics.period_end_date
            ),
            period_type=valuation_metrics.period_type,
            currency=valuation_metrics.currency,
            earnings_yield_score=earnings_yield_score,
            free_cash_flow_yield_score=(
                free_cash_flow_yield_score
            ),
            valuation_score=valuation_score,
            market_cap=valuation_metrics.market_cap,
            enterprise_value=(
                valuation_metrics.enterprise_value
            ),
            price_to_earnings=(
                valuation_metrics.price_to_earnings
            ),
            price_to_sales=(
                valuation_metrics.price_to_sales
            ),
            price_to_book=(
                valuation_metrics.price_to_book
            ),
            ev_to_ebitda=(
                valuation_metrics.ev_to_ebitda
            ),
            free_cash_flow_yield=(
                valuation_metrics.free_cash_flow_yield
            ),
            earnings_yield=(
                valuation_metrics.earnings_yield
            ),
            company_profile_id=(
                valuation_metrics.company_profile_id
            ),
            income_statement_ids=list(
                valuation_metrics.income_statement_ids
            ),
            balance_sheet_id=(
                valuation_metrics.balance_sheet_id
            ),
            cash_flow_statement_ids=list(
                valuation_metrics.cash_flow_statement_ids
            ),
            quarter_end_dates=list(
                valuation_metrics.quarter_end_dates
            ),
            missing_fields=list(
                valuation_metrics.missing_fields
            ),
            confidence=confidence,
        )

    def _calculate_score_coverage(
        self,
        scores: list[Decimal | None],
    ) -> Decimal:
        available_count = sum(
            1
            for score in scores
            if score is not None
        )

        return (
            Decimal(available_count)
            / Decimal(self.SCORE_COMPONENT_COUNT)
        )

    @staticmethod
    def _score_earnings_yield(
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        if value >= Decimal("0.08"):
            return Decimal("1")

        if value >= Decimal("0.05"):
            return Decimal("0.75")

        if value >= Decimal("0.03"):
            return Decimal("0.50")

        if value > Decimal("0"):
            return Decimal("0.25")

        return Decimal("0")

    @staticmethod
    def _score_free_cash_flow_yield(
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        if value >= Decimal("0.06"):
            return Decimal("1")

        if value >= Decimal("0.04"):
            return Decimal("0.75")

        if value >= Decimal("0.02"):
            return Decimal("0.50")

        if value > Decimal("0"):
            return Decimal("0.25")

        return Decimal("0")

    @staticmethod
    def _average_scores(
        scores: list[Decimal | None],
    ) -> Decimal | None:
        available_scores = [
            score
            for score in scores
            if score is not None
        ]

        if not available_scores:
            return None

        return (
            sum(
                available_scores,
                Decimal("0"),
            )
            / Decimal(len(available_scores))
        )