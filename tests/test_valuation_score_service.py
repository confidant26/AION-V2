from decimal import Decimal

import pytest

from app.services.valuation_score_service import (
    ValuationScoreService,
)


@pytest.mark.parametrize(
    ("value", "expected_score"),
    [
        (Decimal("0.10"), Decimal("1")),
        (Decimal("0.08"), Decimal("1")),
        (Decimal("0.0799"), Decimal("0.75")),
        (Decimal("0.05"), Decimal("0.75")),
        (Decimal("0.0499"), Decimal("0.50")),
        (Decimal("0.03"), Decimal("0.50")),
        (Decimal("0.0299"), Decimal("0.25")),
        (Decimal("0.0001"), Decimal("0.25")),
        (Decimal("0"), Decimal("0")),
        (Decimal("-0.01"), Decimal("0")),
        (None, None),
    ],
)
def test_earnings_yield_score_boundaries(
    value,
    expected_score,
):
    result = (
        ValuationScoreService
        ._score_earnings_yield(
            value
        )
    )

    assert result == expected_score


@pytest.mark.parametrize(
    ("value", "expected_score"),
    [
        (Decimal("0.10"), Decimal("1")),
        (Decimal("0.06"), Decimal("1")),
        (Decimal("0.0599"), Decimal("0.75")),
        (Decimal("0.04"), Decimal("0.75")),
        (Decimal("0.0399"), Decimal("0.50")),
        (Decimal("0.02"), Decimal("0.50")),
        (Decimal("0.0199"), Decimal("0.25")),
        (Decimal("0.0001"), Decimal("0.25")),
        (Decimal("0"), Decimal("0")),
        (Decimal("-0.01"), Decimal("0")),
        (None, None),
    ],
)
def test_free_cash_flow_yield_score_boundaries(
    value,
    expected_score,
):
    result = (
        ValuationScoreService
        ._score_free_cash_flow_yield(
            value
        )
    )

    assert result == expected_score


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        (
            [
                Decimal("1"),
                Decimal("0.50"),
            ],
            Decimal("0.75"),
        ),
        (
            [
                Decimal("0.25"),
                Decimal("0.50"),
            ],
            Decimal("0.375"),
        ),
        (
            [
                Decimal("1"),
                None,
            ],
            Decimal("1"),
        ),
        (
            [
                None,
                Decimal("0.50"),
            ],
            Decimal("0.50"),
        ),
        (
            [
                None,
                None,
            ],
            None,
        ),
    ],
)
def test_average_scores(
    scores,
    expected,
):
    result = ValuationScoreService._average_scores(
        scores
    )

    assert result == expected


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        (
            [
                Decimal("1"),
                Decimal("0.50"),
            ],
            Decimal("1"),
        ),
        (
            [
                Decimal("1"),
                None,
            ],
            Decimal("0.5"),
        ),
        (
            [
                None,
                Decimal("0.50"),
            ],
            Decimal("0.5"),
        ),
        (
            [
                None,
                None,
            ],
            Decimal("0"),
        ),
    ],
)
def test_score_coverage(
    scores,
    expected,
):
    service = object.__new__(
        ValuationScoreService
    )

    result = service._calculate_score_coverage(
        scores
    )

    assert result == expected