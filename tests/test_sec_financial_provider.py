from datetime import date

import pytest

from app.core.config import settings
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
            start="2024-10-01",
            end="2025-09-30",
            value=400,
            form="10-K",
            filed="2025-11-01",
        ),
        fact(
            start="2025-10-01",
            end="2026-09-30",
            value=440,
            form="10-K",
            filed="2026-11-01",
        ),
        fact(
            start="2025-10-01",
            end="2025-12-31",
            value=100,
            form="10-Q",
            filed="2026-02-01",
        ),
        fact(
            start="2026-01-01",
            end="2026-03-31",
            value=105,
            form="10-Q",
            filed="2026-05-01",
        ),
        fact(
            start="2026-04-01",
            end="2026-06-30",
            value=110,
            form="10-Q",
            filed="2026-08-01",
        ),
        fact(
            start="2024-10-01",
            end="2024-12-31",
            value=90,
            form="10-Q",
            filed="2025-02-01",
        ),
        fact(
            start="2025-01-01",
            end="2025-03-31",
            value=95,
            form="10-Q",
            filed="2025-05-01",
        ),
        fact(
            start="2025-04-01",
            end="2025-06-30",
            value=100,
            form="10-Q",
            filed="2025-08-01",
        ),
    ]

    net_income = [
        fact(
            start=item["start"],
            end=item["end"],
            value=(
                item["val"]
                / 4
            ),
            form=item["form"],
            filed=item["filed"],
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
            "AAPL": "0000320193",
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
        match="SEC CIK not found",
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

    assert len(annual) == 2

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
                30,
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
            start="2025-10-01",
            end="2026-03-31",
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
                31,
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
        await provider.get_income_statements(
            "AAPL"
        )