from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.schemas.composite_score import CompositeScoreResponse
from app.services.growth_score_service import (
    GrowthScoreService,
)
from app.services.quality_score_service import (
    QualityScoreService,
)
from app.services.valuation_score_service import (
    ValuationScoreService,
)


class CompositeScoreService:
    GROWTH_WEIGHT = Decimal("0.35")
    QUALITY_WEIGHT = Decimal("0.35")
    VALUATION_WEIGHT = Decimal("0.30")

    def __init__(
        self,
        db: Session,
    ):
        self.growth_score_service = GrowthScoreService(db)
        self.quality_score_service = QualityScoreService(db)
        self.valuation_score_service = ValuationScoreService(db)

    def get_composite_score(
        self,
        symbol: str,
    ) -> CompositeScoreResponse:
        clean_symbol = symbol.strip().upper()

        growth_results = (
            self.growth_score_service.get_growth_scores(
                symbol=clean_symbol,
                limit=1,
            )
        )

        quality_results = (
            self.quality_score_service.get_quality_scores(
                symbol=clean_symbol,
                limit=1,
            )
        )

        valuation_result = (
            self.valuation_score_service.get_valuation_score(
                symbol=clean_symbol,
            )
        )

        growth_result = (
            growth_results[0]
            if growth_results
            else None
        )

        quality_result = (
            quality_results[0]
            if quality_results
            else None
        )

        growth_score = (
            growth_result.growth_score
            if growth_result is not None
            else None
        )

        quality_score = (
            quality_result.quality_score
            if quality_result is not None
            else None
        )

        valuation_score = valuation_result.valuation_score

        missing_components: list[str] = []

        if growth_score is None:
            missing_components.append("growth_score")

        if quality_score is None:
            missing_components.append("quality_score")

        if valuation_score is None:
            missing_components.append("valuation_score")

        composite_score = self._weighted_score(
            growth_score=growth_score,
            quality_score=quality_score,
            valuation_score=valuation_score,
        )

        confidence = self._calculate_confidence(
            growth_confidence=(
                growth_result.confidence
                if growth_result is not None
                else Decimal("0")
            ),
            quality_confidence=(
                quality_result.confidence
                if quality_result is not None
                else Decimal("0")
            ),
            valuation_confidence=(
                valuation_result.confidence
            ),
        )

        as_of_date = self._latest_date(
            growth_date=(
                growth_result.period_end_date
                if growth_result is not None
                else None
            ),
            quality_date=(
                quality_result.period_end_date
                if quality_result is not None
                else None
            ),
            valuation_date=(
                valuation_result.period_end_date
            ),
        )

        return CompositeScoreResponse(
            symbol=clean_symbol,
            as_of_date=as_of_date,
            currency=(
                valuation_result.currency
                or (
                    quality_result.currency
                    if quality_result is not None
                    else None
                )
                or (
                    growth_result.currency
                    if growth_result is not None
                    else None
                )
            ),
            growth_score=growth_score,
            quality_score=quality_score,
            valuation_score=valuation_score,
            composite_score=composite_score,
            growth_weight=self.GROWTH_WEIGHT,
            quality_weight=self.QUALITY_WEIGHT,
            valuation_weight=self.VALUATION_WEIGHT,
            growth_period_end_date=(
                growth_result.period_end_date
                if growth_result is not None
                else None
            ),
            quality_period_end_date=(
                quality_result.period_end_date
                if quality_result is not None
                else None
            ),
            valuation_period_end_date=(
                valuation_result.period_end_date
            ),
            missing_components=missing_components,
            confidence=confidence,
        )

    def _weighted_score(
        self,
        *,
        growth_score: Decimal | None,
        quality_score: Decimal | None,
        valuation_score: Decimal | None,
    ) -> Decimal | None:
        weighted_total = Decimal("0")
        active_weight = Decimal("0")

        if growth_score is not None:
            weighted_total += (
                growth_score
                * self.GROWTH_WEIGHT
            )
            active_weight += self.GROWTH_WEIGHT

        if quality_score is not None:
            weighted_total += (
                quality_score
                * self.QUALITY_WEIGHT
            )
            active_weight += self.QUALITY_WEIGHT

        if valuation_score is not None:
            weighted_total += (
                valuation_score
                * self.VALUATION_WEIGHT
            )
            active_weight += self.VALUATION_WEIGHT

        if active_weight == 0:
            return None

        return weighted_total / active_weight

    def _calculate_confidence(
        self,
        *,
        growth_confidence: Decimal,
        quality_confidence: Decimal,
        valuation_confidence: Decimal,
    ) -> Decimal:
        weighted_confidence = (
            growth_confidence
            * self.GROWTH_WEIGHT
            + quality_confidence
            * self.QUALITY_WEIGHT
            + valuation_confidence
            * self.VALUATION_WEIGHT
        )

        if weighted_confidence < Decimal("0"):
            return Decimal("0")

        if weighted_confidence > Decimal("1"):
            return Decimal("1")

        return weighted_confidence

    @staticmethod
    def _latest_date(
        *,
        growth_date: date | None,
        quality_date: date | None,
        valuation_date: date | None,
    ) -> date:
        available_dates = [
            value
            for value in (
                growth_date,
                quality_date,
                valuation_date,
            )
            if value is not None
        ]

        if not available_dates:
            raise ValueError(
                "Composite score date could not be determined."
            )

        return max(available_dates)