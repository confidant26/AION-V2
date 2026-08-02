from decimal import Decimal

import pytest

from app.services.quality_score_service import (
    QualityScoreService,
)


@pytest.mark.parametrize(
    ("margin_value", "expected_score"),
    [
        (Decimal("0.30"), Decimal("1")),
        (Decimal("0.20"), Decimal("1")),
        (Decimal("0.1999"), Decimal("0.75")),
        (Decimal("0.10"), Decimal("0.75")),
        (Decimal("0.0999"), Decimal("0.50")),
        (Decimal("0"), Decimal("0.50")),
        (Decimal("-0.0001"), Decimal("0")),
        (Decimal("-0.50"), Decimal("0")),
        (None, None),
    ],
)
def test_operating_margin_score_boundaries(
    margin_value,
    expected_score,
):
    result = QualityScoreService._score_operating_margin(
        margin_value
    )

    assert result == expected_score

@pytest.mark.parametrize(
    ("margin_value", "expected_score"),
    [
        (Decimal("0.20"), Decimal("1")),
        (Decimal("0.15"), Decimal("1")),
        (Decimal("0.1499"), Decimal("0.75")),
        (Decimal("0.08"), Decimal("0.75")),
        (Decimal("0.0799"), Decimal("0.50")),
        (Decimal("0"), Decimal("0.50")),
        (Decimal("-0.0001"), Decimal("0")),
        (Decimal("-0.50"), Decimal("0")),
        (None, None),
    ],
)
def test_net_margin_score_boundaries(
    margin_value,
    expected_score,
):
    result = QualityScoreService._score_net_margin(
        margin_value
    )

    assert result == expected_score

@pytest.mark.parametrize(
    ("value", "expected_score"),
    [
        (Decimal("0.20"), Decimal("1")),
        (Decimal("0.10"), Decimal("1")),
        (Decimal("0.0999"), Decimal("0.75")),
        (Decimal("0.05"), Decimal("0.75")),
        (Decimal("0.0499"), Decimal("0.50")),
        (Decimal("0.02"), Decimal("0.50")),
        (Decimal("0.0199"), Decimal("0.25")),
        (Decimal("0"), Decimal("0.25")),
        (Decimal("-0.0001"), Decimal("0")),
        (Decimal("-0.50"), Decimal("0")),
        (None, None),
    ],
)
def test_return_on_assets_score_boundaries(
    value,
    expected_score,
):
    result = QualityScoreService._score_return_on_assets(
        value
    )

    assert result == expected_score

@pytest.mark.parametrize(
    ("value", "expected_score"),
    [
        (Decimal("0.30"), Decimal("1")),
        (Decimal("0.20"), Decimal("1")),
        (Decimal("0.1999"), Decimal("0.75")),
        (Decimal("0.10"), Decimal("0.75")),
        (Decimal("0.0999"), Decimal("0.50")),
        (Decimal("0"), Decimal("0.50")),
        (Decimal("-0.0001"), Decimal("0")),
        (Decimal("-0.50"), Decimal("0")),
        (None, None),
    ],
)
def test_return_on_equity_score_boundaries(
    value,
    expected_score,
):
    result = QualityScoreService._score_return_on_equity(
        value
    )

    assert result == expected_score

@pytest.mark.parametrize(
    ("value", "expected_score"),
    [
        (Decimal("2.00"), Decimal("1")),
        (Decimal("1.50"), Decimal("1")),
        (Decimal("3.00"), Decimal("1")),
        (Decimal("1.4999"), Decimal("0.75")),
        (Decimal("1.00"), Decimal("0.75")),
        (Decimal("3.0001"), Decimal("0.75")),
        (Decimal("0.9999"), Decimal("0.50")),
        (Decimal("0.75"), Decimal("0.50")),
        (Decimal("0.7499"), Decimal("0")),
        (Decimal("0"), Decimal("0")),
        (None, None),
    ],
)
def test_current_ratio_score_boundaries(
    value,
    expected_score,
):
    result = QualityScoreService._score_current_ratio(
        value
    )

    assert result == expected_score

@pytest.mark.parametrize(
    ("value", "expected_score"),
    [
        (Decimal("-0.01"), Decimal("0")),
        (Decimal("0"), Decimal("1")),
        (Decimal("0.50"), Decimal("1")),
        (Decimal("0.5001"), Decimal("0.75")),
        (Decimal("1.00"), Decimal("0.75")),
        (Decimal("1.0001"), Decimal("0.50")),
        (Decimal("2.00"), Decimal("0.50")),
        (Decimal("2.0001"), Decimal("0.25")),
        (Decimal("5.00"), Decimal("0.25")),
        (None, None),
    ],
)
def test_debt_to_equity_score_boundaries(
    value,
    expected_score,
):
    result = QualityScoreService._score_debt_to_equity(
        value
    )

    assert result == expected_score

@pytest.mark.parametrize(
    ("value", "expected_score"),
    [
        (Decimal("-0.01"), Decimal("0")),
        (Decimal("0"), Decimal("1")),
        (Decimal("0.50"), Decimal("1")),
        (Decimal("0.5001"), Decimal("0.75")),
        (Decimal("1.00"), Decimal("0.75")),
        (Decimal("1.0001"), Decimal("0.50")),
        (Decimal("2.00"), Decimal("0.50")),
        (Decimal("2.0001"), Decimal("0.25")),
        (Decimal("5.00"), Decimal("0.25")),
        (None, None),
    ],
)
def test_debt_to_equity_score_boundaries(
    value,
    expected_score,
):
    result = QualityScoreService._score_debt_to_equity(
        value
    )

    assert result == expected_score


@pytest.mark.parametrize(
    ("value", "expected_score"),
    [
        (Decimal("0.20"), Decimal("1")),
        (Decimal("0.15"), Decimal("1")),
        (Decimal("0.1499"), Decimal("0.75")),
        (Decimal("0.08"), Decimal("0.75")),
        (Decimal("0.0799"), Decimal("0.50")),
        (Decimal("0"), Decimal("0.50")),
        (Decimal("-0.0001"), Decimal("0")),
        (Decimal("-0.50"), Decimal("0")),
        (None, None),
    ],
)
def test_free_cash_flow_margin_score_boundaries(
    value,
    expected_score,
):
    result = (
        QualityScoreService
        ._score_free_cash_flow_margin(
            value
        )
    )

    assert result == expected_score