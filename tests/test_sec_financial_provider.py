from datetime import date

import pytest

from app.core.config import settings
from app.core.fiscal_period import (
    canonical_period_end_date,
    period_dates_match,
)
from app.providers.financial.factory import (
    create_financial_provider,
)
from app.providers.financial.sec import (
    SecFinancialProvider,
)


def fact(
    *,
    start,
    end,
    value,
    form,
    filed,
):
    return {
        "start": start,
        "end": end,
        "val": value,
        "form": form,
        "filed": filed,
    }


def concept(
    values,
    unit="USD",
):
    return {
        "units": {
            unit: values,
        }
    }


def make_company_facts():
    revenue = [
        fact(
            start="2024-09-29",
            end="2025-09-27",
            value=400,
            form="10-K",
            filed="2025-11-01",
        ),
        fact(
            start="2025-09-28",
            end="2026-09-26",
            value=440,
            form="10-K",
            filed="2026-11-01",
        ),
        fact(
            start="2025-09-28",
            end="2025-12-27",
            value=100,
            form="10-Q",
            filed="2026-02-01",
        ),
        fact(
            start="2025-12-28",
            end="2026-03-28",
            value=105,
            form="10-Q",
            filed="2026-05-01",
        ),
        fact(
            start="2026-03-29",
            end="2026-06-27",
            value=110,
            form="10-Q",
            filed="2026-08-01",
        ),
        fact(
            start="2024-09-29",
            end="2024-12-28",
            value=90,
            form="10-Q",
            filed="2025-02-01",
        ),
        fact(
            start="2024-12-29",
            end="2025-03-29",
            value=95,
            form="10-Q",
            filed="2025-05-01",
        ),
        fact(
            start="2025-03-30",
            end="2025-06-28",
            value=100,
            form="10-Q",
            filed="2025-08-01",
        ),
    ]

    net_income = [
        fact(
            start=item[
                "start"
            ],
            end=item[
                "end"
            ],
            value=(
                item[
                    "val"
                ]
                / 4
            ),
            form=item[
                "form"
            ],
            filed=item[
                "filed"
            ],
        )
        for item in revenue
    ]

    return {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": (
                    concept(
                        revenue
                    )
                ),
                "NetIncomeLoss": (
                    concept(
                        net_income
                    )
                ),
            }
        }
    }


def test_sec_factory_creates_provider():
    provider = (
        create_financial_provider(
            "sec"
        )
    )

    assert isinstance(
        provider,
        SecFinancialProvider,
    )


def test_sec_resolves_cik(
    monkeypatch,
):
    provider = (
        SecFinancialProvider()
    )

    monkeypatch.setattr(
        provider,
        "_ticker_map",
        lambda: {
            "AAPL": (
                "0000320193"
            ),
        },
    )

    assert (
        provider._resolve_cik(
            "AAPL"
        )
        == "0000320193"
    )


def test_sec_missing_cik_raises(
    monkeypatch,
):
    provider = (
        SecFinancialProvider()
    )

    monkeypatch.setattr(
        provider,
        "_ticker_map",
        lambda: {},
    )

    with pytest.raises(
        ValueError,
        match=(
            "SEC CIK not found"
        ),
    ):
        provider._resolve_cik(
            "INVALID"
        )


def test_sec_builds_annual_and_quarterly_statements():
    provider = (
        SecFinancialProvider()
    )

    statements = (
        provider._build_statements(
            make_company_facts()
        )
    )

    annual = [
        statement
        for statement in statements
        if statement[
            "period_type"
        ] == "annual"
    ]

    quarterly = [
        statement
        for statement in statements
        if statement[
            "period_type"
        ] == "quarterly"
    ]

    assert len(
        annual
    ) == 2

    assert len(
        quarterly
    ) >= 4


def test_sec_derives_fourth_quarter():
    provider = (
        SecFinancialProvider()
    )

    statements = (
        provider._build_statements(
            make_company_facts()
        )
    )

    q4 = next(
        statement
        for statement in statements
        if (
            statement[
                "period_type"
            ] == "quarterly"
            and statement[
                "period_end_date"
            ]
            == date(
                2026,
                9,
                26,
            )
        )
    )

    assert (
        q4[
            "total_revenue"
        ]
        == pytest.approx(
            125
        )
    )


def test_sec_ignores_ytd_quarter_fact():
    provider = (
        SecFinancialProvider()
    )

    facts = (
        make_company_facts()
    )

    facts[
        "facts"
    ][
        "us-gaap"
    ][
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    ][
        "units"
    ][
        "USD"
    ].append(
        fact(
            start="2025-09-28",
            end="2026-03-28",
            value=205,
            form="10-Q",
            filed="2026-05-01",
        )
    )

    statements = (
        provider._build_statements(
            facts
        )
    )

    q2 = next(
        statement
        for statement in statements
        if (
            statement[
                "period_type"
            ] == "quarterly"
            and statement[
                "period_end_date"
            ]
            == date(
                2026,
                3,
                28,
            )
        )
    )

    assert (
        q2[
            "total_revenue"
        ]
        == pytest.approx(
            105
        )
    )


@pytest.mark.anyio
async def test_sec_fetch_requires_user_agent(
    monkeypatch,
):
    provider = (
        SecFinancialProvider()
    )

    monkeypatch.setattr(
        settings,
        "sec_user_agent",
        "",
    )

    with pytest.raises(
        ValueError,
        match="SEC_USER_AGENT",
    ):
        await (
            provider
            .get_income_statements(
                "AAPL"
            )
        )


@pytest.mark.parametrize(
    "source_date, expected",
    [
        (
            date(
                2026,
                6,
                27,
            ),
            date(
                2026,
                6,
                30,
            ),
        ),
        (
            date(
                2026,
                3,
                28,
            ),
            date(
                2026,
                3,
                31,
            ),
        ),
        (
            date(
                2025,
                12,
                27,
            ),
            date(
                2025,
                12,
                31,
            ),
        ),
        (
            date(
                2022,
                9,
                24,
            ),
            date(
                2022,
                9,
                30,
            ),
        ),
    ],
)
def test_canonical_period_end_date(
    source_date,
    expected,
):
    assert (
        canonical_period_end_date(
            source_date
        )
        == expected
    )


def test_period_date_can_match_previous_month_end():
    assert (
        canonical_period_end_date(
            date(
                2026,
                7,
                2,
            )
        )
        == date(
            2026,
            6,
            30,
        )
    )


def test_period_date_outside_tolerance_is_preserved():
    source_date = date(
        2026,
        6,
        15,
    )

    assert (
        canonical_period_end_date(
            source_date
        )
        == source_date
    )


def test_period_dates_match_across_providers():
    assert period_dates_match(
        date(
            2026,
            6,
            27,
        ),
        date(
            2026,
            6,
            30,
        ),
    )


def test_sec_normalizes_period_dates():
    provider = (
        SecFinancialProvider()
    )

    statements = [
        {
            "period_type": (
                "quarterly"
            ),
            "period_end_date": date(
                2026,
                6,
                27,
            ),
            "total_revenue": 100,
        },
        {
            "period_type": (
                "quarterly"
            ),
            "period_end_date": date(
                2026,
                3,
                28,
            ),
            "total_revenue": 90,
        },
    ]

    normalized = (
        provider
        ._normalize_period_dates(
            statements
        )
    )

    assert [
        item[
            "period_end_date"
        ]
        for item in normalized
    ] == [
        date(
            2026,
            6,
            30,
        ),
        date(
            2026,
            3,
            31,
        ),
    ]