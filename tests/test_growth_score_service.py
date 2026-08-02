from decimal import Decimal

import pytest

from app.services.growth_score_service import (
    GrowthScoreService,
)


@pytest.mark.parametrize(
    ("growth_value", "expected_score"),
    [
        (Decimal("0.30"), Decimal("1")),
        (Decimal("0.20"), Decimal("1")),
        (Decimal("0.1999"), Decimal("0.75")),
        (Decimal("0.10"), Decimal("0.75")),
        (Decimal("0.0999"), Decimal("0.50")),
        (Decimal("0"), Decimal("0.50")),
        (Decimal("-0.0001"), Decimal("0.25")),
        (Decimal("-0.10"), Decimal("0.25")),
        (Decimal("-0.1001"), Decimal("0")),
        (Decimal("-0.50"), Decimal("0")),
        (None, None),
    ],
)
def test_score_growth_boundaries(
    growth_value,
    expected_score,
):
    result = GrowthScoreService._score_growth(
        growth_value
    )

    assert result == expected_score