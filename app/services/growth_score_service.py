from decimal import Decimal

from sqlalchemy.orm import Session

from app.schemas.growth_score import GrowthScoreResponse
from app.services.growth_metrics_service import (
    GrowthMetricsService,
)


class GrowthScoreService:
    SCORE_COMPONENT_COUNT = 6

    def __init__(
        self,
        db: Session,
    ):
        self.growth_metrics_service = (
            GrowthMetricsService(db)
        )

    def get_growth_scores(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[GrowthScoreResponse]:
        growth_metrics = (
            self.growth_metrics_service.get_growth_metrics(
                symbol=symbol,
                limit=limit,
            )
        )

        results: list[GrowthScoreResponse] = []

        for metrics in growth_metrics:
            revenue_growth_score = self._score_growth(
                metrics.revenue_growth
            )

            operating_income_growth_score = (
                self._score_growth(
                    metrics.operating_income_growth
                )
            )

            net_income_growth_score = self._score_growth(
                metrics.net_income_growth
            )

            free_cash_flow_growth_score = (
                self._score_growth(
                    metrics.free_cash_flow_growth
                )
            )

            total_assets_growth_score = self._score_growth(
                metrics.total_assets_growth
            )

            stockholders_equity_growth_score = (
                self._score_growth(
                    metrics.stockholders_equity_growth
                )
            )

            growth_score = self._average_scores(
                [
                    revenue_growth_score,
                    operating_income_growth_score,
                    net_income_growth_score,
                    free_cash_flow_growth_score,
                    total_assets_growth_score,
                    stockholders_equity_growth_score,
                ]
            )

            score_coverage = self._calculate_score_coverage(
                [
                    revenue_growth_score,
                    operating_income_growth_score,
                    net_income_growth_score,
                    free_cash_flow_growth_score,
                    total_assets_growth_score,
                    stockholders_equity_growth_score,
                ]
            )

            confidence = min(
                metrics.confidence,
                score_coverage,
            )

            results.append(
                GrowthScoreResponse(
                    symbol=metrics.symbol,
                    period_end_date=metrics.period_end_date,
                    previous_period_end_date=(
                        metrics.previous_period_end_date
                    ),
                    period_type=metrics.period_type,
                    currency=metrics.currency,
                    revenue_growth_score=(
                        revenue_growth_score
                    ),
                    operating_income_growth_score=(
                        operating_income_growth_score
                    ),
                    net_income_growth_score=(
                        net_income_growth_score
                    ),
                    free_cash_flow_growth_score=(
                        free_cash_flow_growth_score
                    ),
                    total_assets_growth_score=(
                        total_assets_growth_score
                    ),
                    stockholders_equity_growth_score=(
                        stockholders_equity_growth_score
                    ),
                    growth_score=growth_score,
                    revenue_growth=metrics.revenue_growth,
                    operating_income_growth=(
                        metrics.operating_income_growth
                    ),
                    net_income_growth=(
                        metrics.net_income_growth
                    ),
                    free_cash_flow_growth=(
                        metrics.free_cash_flow_growth
                    ),
                    total_assets_growth=(
                        metrics.total_assets_growth
                    ),
                    stockholders_equity_growth=(
                        metrics.stockholders_equity_growth
                    ),
                    current_income_statement_id=(
                        metrics.current_income_statement_id
                    ),
                    previous_income_statement_id=(
                        metrics.previous_income_statement_id
                    ),
                    current_balance_sheet_id=(
                        metrics.current_balance_sheet_id
                    ),
                    previous_balance_sheet_id=(
                        metrics.previous_balance_sheet_id
                    ),
                    current_cash_flow_statement_id=(
                        metrics.current_cash_flow_statement_id
                    ),
                    previous_cash_flow_statement_id=(
                        metrics.previous_cash_flow_statement_id
                    ),
                    missing_fields=list(
                        metrics.missing_fields
                    ),
                    confidence=confidence,
                )
            )

        return results

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
    def _score_growth(
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        if value >= Decimal("0.20"):
            return Decimal("1")

        if value >= Decimal("0.10"):
            return Decimal("0.75")

        if value >= Decimal("0"):
            return Decimal("0.50")

        if value >= Decimal("-0.10"):
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