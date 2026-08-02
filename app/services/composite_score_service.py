from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
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

    MAX_COMPONENT_DATE_SPREAD_DAYS = 430

    def __init__(
        self,
        db: Session,
    ):
        self.asset_repository = AssetRepository(db)
        self.growth_score_service = GrowthScoreService(db)
        self.quality_score_service = QualityScoreService(db)
        self.valuation_score_service = ValuationScoreService(db)

    def get_composite_score(
        self,
        symbol: str,
    ) -> CompositeScoreResponse:
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(
            clean_symbol
        )

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        growth_result = self._get_growth_result(
            symbol=clean_symbol,
        )

        quality_result = self._get_quality_result(
            symbol=clean_symbol,
        )

        valuation_result = self._get_valuation_result(
            symbol=clean_symbol,
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

        valuation_score = (
            valuation_result.valuation_score
            if valuation_result is not None
            else None
        )

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
                if valuation_result is not None
                else Decimal("0")
            ),
        )

        growth_date = (
            growth_result.period_end_date
            if growth_result is not None
            else None
        )

        quality_date = (
            quality_result.period_end_date
            if quality_result is not None
            else None
        )

        valuation_date = (
            valuation_result.period_end_date
            if valuation_result is not None
            else None
        )

        (
            oldest_component_date,
            newest_component_date,
            component_date_spread_days,
            period_alignment_ok,
        ) = self._calculate_period_alignment(
            growth_date=growth_date,
            quality_date=quality_date,
            valuation_date=valuation_date,
        )

        as_of_date = newest_component_date

        currency = self._resolve_currency(
            growth_result=growth_result,
            quality_result=quality_result,
            valuation_result=valuation_result,
        )

        return CompositeScoreResponse(
            symbol=clean_symbol,
            as_of_date=as_of_date,
            currency=currency,
            growth_score=growth_score,
            quality_score=quality_score,
            valuation_score=valuation_score,
            composite_score=composite_score,
            growth_weight=self.GROWTH_WEIGHT,
            quality_weight=self.QUALITY_WEIGHT,
            valuation_weight=self.VALUATION_WEIGHT,
            growth_period_end_date=growth_date,
            quality_period_end_date=quality_date,
            valuation_period_end_date=valuation_date,
            oldest_component_date=oldest_component_date,
            newest_component_date=newest_component_date,
            component_date_spread_days=(
                component_date_spread_days
            ),
            period_alignment_ok=period_alignment_ok,
            missing_components=missing_components,
            confidence=confidence,
        )

    def _get_growth_result(
        self,
        *,
        symbol: str,
    ):
        try:
            results = (
                self.growth_score_service.get_growth_scores(
                    symbol=symbol,
                    limit=1,
                )
            )
        except ValueError:
            return None

        if not results:
            return None

        return results[0]

    def _get_quality_result(
        self,
        *,
        symbol: str,
    ):
        try:
            results = (
                self.quality_score_service.get_quality_scores(
                    symbol=symbol,
                    limit=1,
                )
            )
        except ValueError:
            return None

        if not results:
            return None

        return results[0]

    def _get_valuation_result(
        self,
        *,
        symbol: str,
    ):
        try:
            return (
                self.valuation_score_service.get_valuation_score(
                    symbol=symbol,
                )
            )
        except ValueError:
            return None

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

    def _calculate_period_alignment(
        self,
        *,
        growth_date: date | None,
        quality_date: date | None,
        valuation_date: date | None,
    ) -> tuple[
        date,
        date,
        int,
        bool,
    ]:
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
                "Composite score could not be calculated because "
                "no scoring components are available."
            )

        oldest_date = min(available_dates)
        newest_date = max(available_dates)

        spread_days = (
            newest_date - oldest_date
        ).days

        alignment_ok = (
            spread_days
            <= self.MAX_COMPONENT_DATE_SPREAD_DAYS
        )

        return (
            oldest_date,
            newest_date,
            spread_days,
            alignment_ok,
        )

    @staticmethod
    def _resolve_currency(
        *,
        growth_result,
        quality_result,
        valuation_result,
    ) -> str | None:
        if (
            valuation_result is not None
            and valuation_result.currency is not None
        ):
            return valuation_result.currency

        if (
            quality_result is not None
            and quality_result.currency is not None
        ):
            return quality_result.currency

        if (
            growth_result is not None
            and growth_result.currency is not None
        ):
            return growth_result.currency

        return None