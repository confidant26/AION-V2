from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.ttm_financials_service import (
    TTMFinancialsService,
)
from app.services.ttm_valuation_metrics_service import (
    TTMValuationMetricsService,
)


def ns(**kwargs):
    return SimpleNamespace(**kwargs)


def make_income(
    *,
    statement_id,
    period_end_date,
    total_revenue="100",
    operating_income="20",
    net_income="15",
    currency="USD",
):
    return ns(
        id=statement_id,
        period_end_date=period_end_date,
        period_type="quarterly",
        currency=currency,
        total_revenue=total_revenue,
        operating_income=operating_income,
        net_income=net_income,
    )


def make_balance(
    *,
    statement_id,
    period_end_date,
    cash="50",
    total_debt="100",
    short_term_debt="20",
    long_term_debt="80",
    equity="300",
    currency="USD",
):
    return ns(
        id=statement_id,
        period_end_date=period_end_date,
        period_type="quarterly",
        currency=currency,
        cash_and_cash_equivalents=cash,
        total_debt=total_debt,
        short_term_debt=short_term_debt,
        long_term_debt=long_term_debt,
        stockholders_equity=equity,
    )


def make_cash_flow(
    *,
    statement_id,
    period_end_date,
    operating_cash_flow="25",
    capital_expenditure="-5",
    free_cash_flow="20",
    depreciation_and_amortization="3",
):
    return ns(
        id=statement_id,
        period_end_date=period_end_date,
        period_type="quarterly",
        currency="USD",
        operating_cash_flow=operating_cash_flow,
        capital_expenditure=capital_expenditure,
        free_cash_flow=free_cash_flow,
        depreciation_and_amortization=(
            depreciation_and_amortization
        ),
    )


def make_matched_quarters():
    dates = [
        date(2025, 12, 31),
        date(2025, 9, 30),
        date(2025, 6, 30),
        date(2025, 3, 31),
    ]

    rows = []

    for index, period_end_date in enumerate(
        dates,
        start=1,
    ):
        rows.append(
            (
                make_income(
                    statement_id=index,
                    period_end_date=period_end_date,
                ),
                make_balance(
                    statement_id=100 + index,
                    period_end_date=period_end_date,
                ),
                make_cash_flow(
                    statement_id=200 + index,
                    period_end_date=period_end_date,
                ),
            )
        )

    return rows


def make_ttm_service(
    *,
    asset=None,
    matched_quarters=None,
):
    service = object.__new__(
        TTMFinancialsService
    )

    if asset is None:
        asset = ns(
            id=1,
            symbol="AAPL",
        )

    if matched_quarters is None:
        matched_quarters = (
            make_matched_quarters()
        )

    service.asset_repository = ns(
        get_by_symbol=lambda symbol: asset
    )

    service.ttm_financials_repository = ns(
        get_latest_matched_quarters=(
            lambda **kwargs: matched_quarters
        )
    )

    return service


def test_ttm_financials_success():
    service = make_ttm_service()

    result = service.get_ttm_financials(
        " aapl "
    )

    assert result.symbol == "AAPL"
    assert result.period_end_date == date(
        2025,
        12,
        31,
    )
    assert result.currency == "USD"
    assert result.total_revenue == Decimal("400")
    assert result.operating_income == Decimal("80")
    assert result.net_income == Decimal("60")
    assert result.operating_cash_flow == Decimal("100")
    assert result.capital_expenditure == Decimal("-20")
    assert result.free_cash_flow == Decimal("80")
    assert (
        result.depreciation_and_amortization
        == Decimal("12")
    )
    assert result.ebitda == Decimal("92")
    assert (
        result.cash_and_cash_equivalents
        == Decimal("50")
    )
    assert result.total_debt == Decimal("100")
    assert (
        result.stockholders_equity
        == Decimal("300")
    )
    assert result.income_statement_ids == [
        1,
        2,
        3,
        4,
    ]
    assert result.cash_flow_statement_ids == [
        201,
        202,
        203,
        204,
    ]
    assert result.balance_sheet_id == 101
    assert result.missing_fields == []
    assert result.confidence == Decimal("1")


def test_ttm_financials_asset_not_found():
    service = make_ttm_service()

    service.asset_repository = ns(
        get_by_symbol=lambda symbol: None
    )

    with pytest.raises(
        ValueError,
        match="Asset not found",
    ):
        service.get_ttm_financials(
            "INVALID"
        )


@pytest.mark.parametrize(
    "quarter_count",
    [
        0,
        1,
        2,
        3,
    ],
)
def test_ttm_financials_requires_four_quarters(
    quarter_count,
):
    rows = make_matched_quarters()[
        :quarter_count
    ]

    service = make_ttm_service(
        matched_quarters=rows,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Four matched quarterly "
            "financial periods"
        ),
    ):
        service.get_ttm_financials(
            "AAPL"
        )


def test_ttm_financials_rejects_duplicate_quarters():
    rows = make_matched_quarters()

    rows[1][0].period_end_date = (
        rows[0][0].period_end_date
    )

    service = make_ttm_service(
        matched_quarters=rows,
    )

    with pytest.raises(
        ValueError,
        match="not unique",
    ):
        service.get_ttm_financials(
            "AAPL"
        )


def test_ttm_financials_rejects_non_consecutive_quarters():
    rows = make_matched_quarters()

    rows[1][0].period_end_date = date(
        2025,
        7,
        1,
    )

    service = make_ttm_service(
        matched_quarters=rows,
    )

    with pytest.raises(
        ValueError,
        match="not consecutive",
    ):
        service.get_ttm_financials(
            "AAPL"
        )


def test_ttm_financials_uses_debt_fallback():
    rows = make_matched_quarters()

    latest_balance = rows[0][1]

    latest_balance.total_debt = None
    latest_balance.short_term_debt = "30"
    latest_balance.long_term_debt = "90"

    service = make_ttm_service(
        matched_quarters=rows,
    )

    result = service.get_ttm_financials(
        "AAPL"
    )

    assert result.total_debt == Decimal("120")
    assert (
        "total_debt"
        not in result.missing_fields
    )


def test_ttm_financials_tracks_missing_total_debt():
    rows = make_matched_quarters()

    latest_balance = rows[0][1]

    latest_balance.total_debt = None
    latest_balance.short_term_debt = None
    latest_balance.long_term_debt = "90"

    service = make_ttm_service(
        matched_quarters=rows,
    )

    result = service.get_ttm_financials(
        "AAPL"
    )

    assert result.total_debt is None
    assert (
        "total_debt"
        in result.missing_fields
    )
    assert result.confidence == Decimal("0.9")


def test_ttm_financials_tracks_missing_summed_field():
    rows = make_matched_quarters()

    rows[2][0].net_income = None

    service = make_ttm_service(
        matched_quarters=rows,
    )

    result = service.get_ttm_financials(
        "AAPL"
    )

    assert result.net_income is None
    assert (
        "net_income"
        in result.missing_fields
    )
    assert result.confidence == Decimal("0.9")


def test_ttm_financials_missing_operating_income_removes_ebitda():
    rows = make_matched_quarters()

    rows[1][0].operating_income = None

    service = make_ttm_service(
        matched_quarters=rows,
    )

    result = service.get_ttm_financials(
        "AAPL"
    )

    assert result.operating_income is None
    assert result.ebitda is None
    assert (
        "operating_income"
        in result.missing_fields
    )


def test_sum_field_success():
    records = [
        ns(value="1.5"),
        ns(value=2),
        ns(value=Decimal("3.5")),
    ]

    missing_fields = []

    result = TTMFinancialsService._sum_field(
        records=records,
        field_name="value",
        missing_fields=missing_fields,
    )

    assert result == Decimal("7.0")
    assert missing_fields == []


def test_sum_field_returns_none_for_invalid_value():
    records = [
        ns(value="10"),
        ns(value="invalid"),
    ]

    missing_fields = []

    result = TTMFinancialsService._sum_field(
        records=records,
        field_name="value",
        missing_fields=missing_fields,
    )

    assert result is None
    assert missing_fields == ["value"]


@pytest.mark.parametrize(
    "operating_income,depreciation,expected",
    [
        (
            Decimal("100"),
            Decimal("20"),
            Decimal("120"),
        ),
        (
            None,
            Decimal("20"),
            None,
        ),
        (
            Decimal("100"),
            None,
            None,
        ),
    ],
)
def test_calculate_ebitda(
    operating_income,
    depreciation,
    expected,
):
    result = (
        TTMFinancialsService
        ._calculate_ebitda(
            operating_income=operating_income,
            depreciation_and_amortization=(
                depreciation
            ),
        )
    )

    assert result == expected


def make_ttm_financials_response(
    **overrides,
):
    values = {
        "symbol": "AAPL",
        "period_end_date": date(
            2025,
            12,
            31,
        ),
        "currency": "USD",
        "total_revenue": Decimal("1000"),
        "operating_income": Decimal("200"),
        "net_income": Decimal("100"),
        "operating_cash_flow": Decimal("180"),
        "capital_expenditure": Decimal("-50"),
        "free_cash_flow": Decimal("130"),
        "depreciation_and_amortization": (
            Decimal("40")
        ),
        "ebitda": Decimal("240"),
        "cash_and_cash_equivalents": (
            Decimal("200")
        ),
        "total_debt": Decimal("300"),
        "stockholders_equity": Decimal("500"),
        "quarter_end_dates": [
            date(2025, 12, 31),
            date(2025, 9, 30),
            date(2025, 6, 30),
            date(2025, 3, 31),
        ],
        "income_statement_ids": [
            1,
            2,
            3,
            4,
        ],
        "cash_flow_statement_ids": [
            11,
            12,
            13,
            14,
        ],
        "balance_sheet_id": 21,
        "missing_fields": [],
        "confidence": Decimal("1"),
    }

    values.update(overrides)

    return ns(**values)


def make_valuation_service(
    *,
    asset=None,
    company_profile=None,
    ttm_financials=None,
):
    service = object.__new__(
        TTMValuationMetricsService
    )

    if asset is None:
        asset = ns(
            id=1,
            symbol="AAPL",
        )

    if company_profile is None:
        company_profile = ns(
            id=10,
            asset_id=1,
            market_cap=2000,
            currency="USD",
        )

    if ttm_financials is None:
        ttm_financials = (
            make_ttm_financials_response()
        )

    service.asset_repository = ns(
        get_by_symbol=lambda symbol: asset
    )

    service.company_profile_repository = ns(
        get_by_asset_id=(
            lambda asset_id: company_profile
        )
    )

    service.ttm_financials_service = ns(
        get_ttm_financials=(
            lambda symbol: ttm_financials
        )
    )

    return service


def test_ttm_valuation_metrics_success():
    service = make_valuation_service()

    result = (
        service
        .get_ttm_valuation_metrics(
            " aapl "
        )
    )

    assert result.symbol == "AAPL"
    assert result.period_type == "ttm"
    assert result.currency == "USD"
    assert result.market_cap == Decimal("2000")
    assert (
        result.enterprise_value
        == Decimal("2100")
    )
    assert (
        result.price_to_earnings
        == Decimal("20")
    )
    assert (
        result.price_to_sales
        == Decimal("2")
    )
    assert (
        result.price_to_book
        == Decimal("4")
    )
    assert (
        result.ev_to_ebitda
        == Decimal("8.75")
    )
    assert (
        result.free_cash_flow_yield
        == Decimal("0.065")
    )
    assert (
        result.earnings_yield
        == Decimal("0.05")
    )
    assert result.company_profile_id == 10
    assert result.balance_sheet_id == 21
    assert result.missing_fields == []
    assert result.confidence == Decimal("1")


def test_ttm_valuation_asset_not_found():
    service = make_valuation_service()

    service.asset_repository = ns(
        get_by_symbol=lambda symbol: None
    )

    with pytest.raises(
        ValueError,
        match="Asset not found",
    ):
        service.get_ttm_valuation_metrics(
            "INVALID"
        )


def test_ttm_valuation_company_profile_not_found():
    service = make_valuation_service()

    service.company_profile_repository = ns(
        get_by_asset_id=lambda asset_id: None
    )

    with pytest.raises(
        ValueError,
        match="Company profile not found",
    ):
        service.get_ttm_valuation_metrics(
            "AAPL"
        )


def test_ttm_valuation_missing_market_cap():
    company_profile = ns(
        id=10,
        asset_id=1,
        market_cap=None,
        currency="USD",
    )

    service = make_valuation_service(
        company_profile=company_profile,
    )

    result = (
        service
        .get_ttm_valuation_metrics(
            "AAPL"
        )
    )

    assert result.market_cap is None
    assert result.enterprise_value is None
    assert result.price_to_earnings is None
    assert result.price_to_sales is None
    assert result.price_to_book is None
    assert result.free_cash_flow_yield is None
    assert result.earnings_yield is None
    assert (
        "market_cap"
        in result.missing_fields
    )
    assert (
        result.confidence
        == Decimal(10) / Decimal(11)
    )


def test_ttm_valuation_propagates_missing_fields():
    ttm_financials = (
        make_ttm_financials_response(
            missing_fields=[
                "net_income"
            ],
            net_income=None,
            confidence=Decimal("0.9"),
        )
    )

    service = make_valuation_service(
        ttm_financials=ttm_financials,
    )

    result = (
        service
        .get_ttm_valuation_metrics(
            "AAPL"
        )
    )

    assert (
        "net_income"
        in result.missing_fields
    )
    assert result.price_to_earnings is None
    assert result.earnings_yield is None
    assert (
        result.confidence
        == Decimal(10) / Decimal(11)
    )


@pytest.mark.parametrize(
    "numerator,denominator,expected",
    [
        (
            Decimal("10"),
            Decimal("2"),
            Decimal("5"),
        ),
        (
            Decimal("10"),
            Decimal("0"),
            None,
        ),
        (
            None,
            Decimal("2"),
            None,
        ),
        (
            Decimal("10"),
            None,
            None,
        ),
    ],
)
def test_ttm_valuation_safe_divide(
    numerator,
    denominator,
    expected,
):
    result = (
        TTMValuationMetricsService
        ._safe_divide(
            numerator,
            denominator,
        )
    )

    assert result == expected


@pytest.mark.parametrize(
    "market_cap,total_debt,cash,expected",
    [
        (
            Decimal("1000"),
            Decimal("300"),
            Decimal("200"),
            Decimal("1100"),
        ),
        (
            None,
            Decimal("300"),
            Decimal("200"),
            None,
        ),
        (
            Decimal("1000"),
            None,
            Decimal("200"),
            None,
        ),
        (
            Decimal("1000"),
            Decimal("300"),
            None,
            None,
        ),
    ],
)
def test_ttm_valuation_enterprise_value(
    market_cap,
    total_debt,
    cash,
    expected,
):
    result = (
        TTMValuationMetricsService
        ._calculate_enterprise_value(
            market_cap=market_cap,
            total_debt=total_debt,
            cash_and_cash_equivalents=cash,
        )
    )

    assert result == expected


def test_ttm_valuation_currency_falls_back_to_financials():
    company_profile = ns(
        id=10,
        asset_id=1,
        market_cap=2000,
        currency=None,
    )

    financials = (
        make_ttm_financials_response(
            currency="EUR",
        )
    )

    service = make_valuation_service(
        company_profile=company_profile,
        ttm_financials=financials,
    )

    result = (
        service
        .get_ttm_valuation_metrics(
            "AAPL"
        )
    )

    assert result.currency == "EUR"