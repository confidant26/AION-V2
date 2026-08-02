from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.composite_score_service import (
    CompositeScoreService,
)


class FakeAssetRepository:
    def get_by_symbol(
        self,
        symbol: str,
    ):
        return SimpleNamespace(
            id=1,
            symbol=symbol,
        )


class MissingGrowthScoreService:
    def get_growth_scores(
        self,
        symbol: str,
        limit: int = 1,
    ):
        raise ValueError(
            f"Growth score not available for symbol: {symbol}"
        )


class FakeGrowthScoreService:
    def get_growth_scores(
        self,
        symbol: str,
        limit: int = 1,
    ):
        return [
            SimpleNamespace(
                symbol=symbol,
                growth_score=Decimal("0.60"),
                confidence=Decimal("1"),
                period_end_date=date(2025, 9, 30),
                currency="USD",
            )
        ]


class MissingQualityScoreService:
    def get_quality_scores(
        self,
        symbol: str,
        limit: int = 1,
    ):
        raise ValueError(
            f"Quality score not available for symbol: {symbol}"
        )


class FakeQualityScoreService:
    def get_quality_scores(
        self,
        symbol: str,
        limit: int = 1,
    ):
        return [
            SimpleNamespace(
                symbol=symbol,
                quality_score=Decimal("0.80"),
                confidence=Decimal("1"),
                period_end_date=date(2025, 9, 30),
                currency="USD",
            )
        ]


class MissingValuationScoreService:
    def get_valuation_score(
        self,
        symbol: str,
    ):
        raise ValueError(
            f"Valuation score not available for symbol: {symbol}"
        )


class FakeValuationScoreService:
    def get_valuation_score(
        self,
        symbol: str,
    ):
        return SimpleNamespace(
            symbol=symbol,
            valuation_score=Decimal("0.40"),
            confidence=Decimal("1"),
            period_end_date=date(2026, 3, 31),
            currency="USD",
        )


def test_composite_score_survives_missing_growth_component():
    service = object.__new__(
        CompositeScoreService
    )

    service.asset_repository = FakeAssetRepository()
    service.growth_score_service = (
        MissingGrowthScoreService()
    )
    service.quality_score_service = (
        FakeQualityScoreService()
    )
    service.valuation_score_service = (
        FakeValuationScoreService()
    )

    result = service.get_composite_score(
        symbol="AAPL",
    )

    expected_composite_score = (
        Decimal("0.80") * Decimal("0.35")
        + Decimal("0.40") * Decimal("0.30")
    ) / Decimal("0.65")

    assert result.symbol == "AAPL"

    assert result.growth_score is None
    assert result.quality_score == Decimal("0.80")
    assert result.valuation_score == Decimal("0.40")

    assert result.composite_score == (
        expected_composite_score
    )

    assert result.missing_components == [
        "growth_score"
    ]

    assert result.confidence == Decimal("0.65")

    assert result.oldest_component_date == date(
        2025,
        9,
        30,
    )

    assert result.newest_component_date == date(
        2026,
        3,
        31,
    )

    assert result.component_date_spread_days == 182
    assert result.period_alignment_ok is True


def test_composite_score_survives_missing_quality_component():
    service = object.__new__(
        CompositeScoreService
    )

    service.asset_repository = FakeAssetRepository()
    service.growth_score_service = (
        FakeGrowthScoreService()
    )
    service.quality_score_service = (
        MissingQualityScoreService()
    )
    service.valuation_score_service = (
        FakeValuationScoreService()
    )

    result = service.get_composite_score(
        symbol="AAPL",
    )

    expected_composite_score = (
        Decimal("0.60") * Decimal("0.35")
        + Decimal("0.40") * Decimal("0.30")
    ) / Decimal("0.65")

    assert result.symbol == "AAPL"

    assert result.growth_score == Decimal("0.60")
    assert result.quality_score is None
    assert result.valuation_score == Decimal("0.40")

    assert result.composite_score == (
        expected_composite_score
    )

    assert result.missing_components == [
        "quality_score"
    ]

    assert result.confidence == Decimal("0.65")

    assert result.oldest_component_date == date(
        2025,
        9,
        30,
    )

    assert result.newest_component_date == date(
        2026,
        3,
        31,
    )

    assert result.component_date_spread_days == 182
    assert result.period_alignment_ok is True


def test_composite_score_survives_missing_valuation_component():
    service = object.__new__(
        CompositeScoreService
    )

    service.asset_repository = FakeAssetRepository()
    service.growth_score_service = (
        FakeGrowthScoreService()
    )
    service.quality_score_service = (
        FakeQualityScoreService()
    )
    service.valuation_score_service = (
        MissingValuationScoreService()
    )

    result = service.get_composite_score(
        symbol="AAPL",
    )

    expected_composite_score = (
        Decimal("0.60") * Decimal("0.35")
        + Decimal("0.80") * Decimal("0.35")
    ) / Decimal("0.70")

    assert result.symbol == "AAPL"

    assert result.growth_score == Decimal("0.60")
    assert result.quality_score == Decimal("0.80")
    assert result.valuation_score is None

    assert result.composite_score == (
        expected_composite_score
    )

    assert result.missing_components == [
        "valuation_score"
    ]

    assert result.confidence == Decimal("0.70")

    assert result.oldest_component_date == date(
        2025,
        9,
        30,
    )

    assert result.newest_component_date == date(
        2025,
        9,
        30,
    )

    assert result.component_date_spread_days == 0
    assert result.period_alignment_ok is True

    import pytest


def test_composite_score_fails_when_all_components_are_missing():
    service = object.__new__(
        CompositeScoreService
    )

    service.asset_repository = FakeAssetRepository()
    service.growth_score_service = (
        MissingGrowthScoreService()
    )
    service.quality_score_service = (
        MissingQualityScoreService()
    )
    service.valuation_score_service = (
        MissingValuationScoreService()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Composite score could not be calculated because "
            "no scoring components are available."
        ),
    ):
        service.get_composite_score(
            symbol="AAPL",
        )

def test_composite_score_uses_expected_weights():
    service = object.__new__(
        CompositeScoreService
    )

    service.asset_repository = FakeAssetRepository()
    service.growth_score_service = (
        FakeGrowthScoreService()
    )
    service.quality_score_service = (
        FakeQualityScoreService()
    )
    service.valuation_score_service = (
        FakeValuationScoreService()
    )

    result = service.get_composite_score(
        symbol="AAPL",
    )

    expected_composite_score = (
        Decimal("0.60") * Decimal("0.35")
        + Decimal("0.80") * Decimal("0.35")
        + Decimal("0.40") * Decimal("0.30")
    )

    assert result.symbol == "AAPL"

    assert result.growth_score == Decimal("0.60")
    assert result.quality_score == Decimal("0.80")
    assert result.valuation_score == Decimal("0.40")

    assert result.growth_weight == Decimal("0.35")
    assert result.quality_weight == Decimal("0.35")
    assert result.valuation_weight == Decimal("0.30")

    assert result.composite_score == (
        expected_composite_score
    )

    assert result.missing_components == []
    assert result.confidence == Decimal("1.00")

    assert result.oldest_component_date == date(
        2025,
        9,
        30,
    )

    assert result.newest_component_date == date(
        2026,
        3,
        31,
    )

    assert result.component_date_spread_days == 182
    assert result.period_alignment_ok is True