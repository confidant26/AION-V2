from decimal import Decimal

from sqlalchemy.orm import Session

from app.schemas.quality_score import QualityScoreResponse
from app.services.financial_metrics_service import (
    FinancialMetricsService,
)


class QualityScoreService:
    def __init__(
        self,
        db: Session,
    ):
        self.financial_metrics_service = (
            FinancialMetricsService(db)
        )

    def get_quality_scores(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[QualityScoreResponse]:
        financial_metrics = (
            self.financial_metrics_service.get_financial_metrics(
                symbol=symbol,
                period_type="annual",
                limit=limit,
            )
        )

        results: list[QualityScoreResponse] = []

        for metrics in financial_metrics:
            profitability_score = self._average_scores(
                [
                    self._score_operating_margin(
                        metrics.operating_margin
                    ),
                    self._score_net_margin(
                        metrics.net_margin
                    ),
                    self._score_return_on_assets(
                        metrics.return_on_assets
                    ),
                    self._score_return_on_equity(
                        metrics.return_on_equity
                    ),
                ]
            )

            balance_sheet_score = self._average_scores(
                [
                    self._score_current_ratio(
                        metrics.current_ratio
                    ),
                    self._score_debt_to_equity(
                        metrics.debt_to_equity
                    ),
                ]
            )

            cash_flow_score = self._average_scores(
                [
                    self._score_free_cash_flow_margin(
                        metrics.free_cash_flow_margin
                    ),
                ]
            )

            quality_score = self._average_scores(
                [
                    profitability_score,
                    balance_sheet_score,
                    cash_flow_score,
                ]
            )

            results.append(
                QualityScoreResponse(
                    symbol=metrics.symbol,
                    period_end_date=metrics.period_end_date,
                    period_type=metrics.period_type,
                    currency=metrics.currency,
                    profitability_score=profitability_score,
                    balance_sheet_score=balance_sheet_score,
                    cash_flow_score=cash_flow_score,
                    quality_score=quality_score,
                    operating_margin=metrics.operating_margin,
                    net_margin=metrics.net_margin,
                    return_on_assets=metrics.return_on_assets,
                    return_on_equity=metrics.return_on_equity,
                    current_ratio=metrics.current_ratio,
                    debt_to_equity=metrics.debt_to_equity,
                    free_cash_flow_margin=(
                        metrics.free_cash_flow_margin
                    ),
                    income_statement_id=(
                        metrics.income_statement_id
                    ),
                    balance_sheet_id=(
                        metrics.balance_sheet_id
                    ),
                    cash_flow_statement_id=(
                        metrics.cash_flow_statement_id
                    ),
                    missing_fields=list(
                        metrics.missing_fields
                    ),
                    confidence=metrics.confidence,
                )
            )

        return results

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

    @staticmethod
    def _score_operating_margin(
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

        return Decimal("0")

    @staticmethod
    def _score_net_margin(
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        if value >= Decimal("0.15"):
            return Decimal("1")

        if value >= Decimal("0.08"):
            return Decimal("0.75")

        if value >= Decimal("0"):
            return Decimal("0.50")

        return Decimal("0")

    @staticmethod
    def _score_return_on_assets(
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        if value >= Decimal("0.10"):
            return Decimal("1")

        if value >= Decimal("0.05"):
            return Decimal("0.75")

        if value >= Decimal("0.02"):
            return Decimal("0.50")

        if value >= Decimal("0"):
            return Decimal("0.25")

        return Decimal("0")

    @staticmethod
    def _score_return_on_equity(
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

        return Decimal("0")

    @staticmethod
    def _score_current_ratio(
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        if (
            Decimal("1.50")
            <= value
            <= Decimal("3.00")
        ):
            return Decimal("1")

        if (
            Decimal("1.00")
            <= value
            < Decimal("1.50")
        ):
            return Decimal("0.75")

        if value > Decimal("3.00"):
            return Decimal("0.75")

        if value >= Decimal("0.75"):
            return Decimal("0.50")

        return Decimal("0")

    @staticmethod
    def _score_debt_to_equity(
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        if value < Decimal("0"):
            return Decimal("0")

        if value <= Decimal("0.50"):
            return Decimal("1")

        if value <= Decimal("1.00"):
            return Decimal("0.75")

        if value <= Decimal("2.00"):
            return Decimal("0.50")

        return Decimal("0.25")

    @staticmethod
    def _score_free_cash_flow_margin(
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        if value >= Decimal("0.15"):
            return Decimal("1")

        if value >= Decimal("0.08"):
            return Decimal("0.75")

        if value >= Decimal("0"):
            return Decimal("0.50")

        return Decimal("0")