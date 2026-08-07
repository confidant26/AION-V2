from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.asset_repository import AssetRepository
from app.schemas.ranking import RankingItem
from app.services.composite_score_service import (
    CompositeScoreService,
)


class RankingService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.asset_repository = (
            AssetRepository(db)
        )

        self.composite_score_service = (
            CompositeScoreService(db)
        )

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    def _score_asset(
        self,
        asset,
    ) -> RankingItem | None:
        try:
            score = (
                self.composite_score_service
                .get_composite_score(
                    symbol=asset.symbol,
                )
            )

        except ValueError:
            return None

        if score.composite_score is None:
            return None

        return RankingItem(
            asset_id=asset.id,
            symbol=asset.symbol,
            name=asset.name,
            asset_type=asset.asset_type,
            exchange=asset.exchange,
            market=asset.market,
            currency=(
                score.currency
                or asset.currency
            ),
            country=asset.country,
            sector=asset.sector,
            industry=asset.industry,
            as_of_date=score.as_of_date,
            growth_score=score.growth_score,
            quality_score=score.quality_score,
            valuation_score=(
                score.valuation_score
            ),
            composite_score=(
                score.composite_score
            ),
            confidence=score.confidence,
            period_alignment_ok=(
                score.period_alignment_ok
            ),
            component_date_spread_days=(
                score.component_date_spread_days
            ),
            missing_components=list(
                score.missing_components
            ),
        )

    @staticmethod
    def _sort_items(
        items: list[RankingItem],
    ) -> list[RankingItem]:
        return sorted(
            items,
            key=lambda item: (
                -item.composite_score,
                -item.confidence,
                item.symbol,
            ),
        )

    def _load_scored_assets(
        self,
        *,
        sector: str | None = None,
        market: str | None = None,
        country: str | None = None,
        asset_type: str | None = None,
    ) -> list[RankingItem]:
        sector = self._normalize_optional_text(
            sector
        )

        market = self._normalize_optional_text(
            market
        )

        country = self._normalize_optional_text(
            country
        )

        asset_type = self._normalize_optional_text(
            asset_type
        )

        if market is not None:
            market = market.upper()

        if country is not None:
            country = country.upper()

        if asset_type is not None:
            asset_type = asset_type.lower()

        assets = (
            self.asset_repository
            .list_filtered_assets(
                active_only=True,
                sector=sector,
                market=market,
                country=country,
                asset_type=asset_type,
            )
        )

        results: list[RankingItem] = []

        for asset in assets:
            item = self._score_asset(
                asset
            )

            if item is not None:
                results.append(
                    item
                )

        return self._sort_items(
            results
        )

    def get_ranking(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        min_confidence: Decimal = Decimal("0"),
    ) -> tuple[
        list[RankingItem],
        int,
    ]:
        items = self._load_scored_assets()

        items = [
            item
            for item in items
            if item.confidence
            >= min_confidence
        ]

        total = len(
            items
        )

        return (
            items[
                offset:
                offset + limit
            ],
            total,
        )

    def screen(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        sector: str | None = None,
        market: str | None = None,
        country: str | None = None,
        asset_type: str | None = None,
        min_growth_score: Decimal | None = None,
        min_quality_score: Decimal | None = None,
        min_valuation_score: Decimal | None = None,
        min_composite_score: Decimal | None = None,
        min_confidence: Decimal | None = None,
        alignment_ok: bool | None = None,
    ) -> tuple[
        list[RankingItem],
        int,
    ]:
        items = self._load_scored_assets(
            sector=sector,
            market=market,
            country=country,
            asset_type=asset_type,
        )

        filtered: list[RankingItem] = []

        for item in items:
            if (
                min_growth_score is not None
                and (
                    item.growth_score is None
                    or item.growth_score
                    < min_growth_score
                )
            ):
                continue

            if (
                min_quality_score is not None
                and (
                    item.quality_score is None
                    or item.quality_score
                    < min_quality_score
                )
            ):
                continue

            if (
                min_valuation_score is not None
                and (
                    item.valuation_score is None
                    or item.valuation_score
                    < min_valuation_score
                )
            ):
                continue

            if (
                min_composite_score is not None
                and item.composite_score
                < min_composite_score
            ):
                continue

            if (
                min_confidence is not None
                and item.confidence
                < min_confidence
            ):
                continue

            if (
                alignment_ok is not None
                and item.period_alignment_ok
                is not alignment_ok
            ):
                continue

            filtered.append(
                item
            )

        total = len(
            filtered
        )

        return (
            filtered[
                offset:
                offset + limit
            ],
            total,
        )