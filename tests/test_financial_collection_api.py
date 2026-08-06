from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def statement(
    period_end_date,
    period_type,
):
    return SimpleNamespace(
        period_end_date=period_end_date,
        period_type=period_type,
    )


class FakeIncomeStatementService:
    def __init__(
        self,
        db,
        provider,
    ):
        pass

    async def collect_income_statements(
        self,
        symbol,
    ):
        return [
            statement(
                date(2026, 6, 30),
                "quarterly",
            ),
            statement(
                date(2025, 9, 30),
                "annual",
            ),
        ]


class FakeBalanceSheetService:
    def __init__(
        self,
        db,
    ):
        pass

    async def collect_balance_sheets(
        self,
        symbol,
    ):
        return [
            statement(
                date(2026, 6, 30),
                "quarterly",
            ),
            statement(
                date(2026, 3, 31),
                "quarterly",
            ),
            statement(
                date(2025, 9, 30),
                "annual",
            ),
        ]


class FakeCashFlowStatementService:
    def __init__(
        self,
        db,
    ):
        pass

    async def collect_cash_flow_statements(
        self,
        symbol,
    ):
        return [
            statement(
                date(2026, 6, 30),
                "quarterly",
            ),
            statement(
                date(2026, 3, 31),
                "quarterly",
            ),
            statement(
                date(2025, 12, 31),
                "quarterly",
            ),
            statement(
                date(2025, 9, 30),
                "annual",
            ),
        ]


class FakeLaggingCashFlowStatementService:
    def __init__(
        self,
        db,
    ):
        pass

    async def collect_cash_flow_statements(
        self,
        symbol,
    ):
        return [
            statement(
                date(2026, 3, 31),
                "quarterly",
            ),
            statement(
                date(2025, 12, 31),
                "quarterly",
            ),
            statement(
                date(2025, 9, 30),
                "annual",
            ),
        ]


def test_financial_collection_endpoint_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.IncomeStatementService",
        FakeIncomeStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.BalanceSheetService",
        FakeBalanceSheetService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.CashFlowStatementService",
        FakeCashFlowStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.get_financial_data_provider",
        lambda: object(),
    )

    response = client.post(
        "/financials/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["symbol"] == "AAPL"

    assert body["counts"] == {
        "income_statements": 2,
        "balance_sheets": 3,
        "cash_flow_statements": 4,
    }

    assert body["total_count"] == 9

    assert body["latest_periods"] == {
        "income_statements": "2026-06-30",
        "balance_sheets": "2026-06-30",
        "cash_flow_statements": "2026-06-30",
    }

    assert body["latest_quarterly_periods"] == {
        "income_statements": "2026-06-30",
        "balance_sheets": "2026-06-30",
        "cash_flow_statements": "2026-06-30",
    }

    assert body["quarterly_alignment"] == {
        "ok": True,
        "spread_days": 0,
    }

    assert body["data_quality"] == {
        "status": "healthy",
        "warnings": [],
    }


def test_financial_collection_endpoint_warns_on_misalignment(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.IncomeStatementService",
        FakeIncomeStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.BalanceSheetService",
        FakeBalanceSheetService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.CashFlowStatementService",
        FakeLaggingCashFlowStatementService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.get_financial_data_provider",
        lambda: object(),
    )

    response = client.post(
        "/financials/collect/aapl"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["latest_quarterly_periods"] == {
        "income_statements": "2026-06-30",
        "balance_sheets": "2026-06-30",
        "cash_flow_statements": "2026-03-31",
    }

    assert body["quarterly_alignment"] == {
        "ok": False,
        "spread_days": 91,
    }

    assert body["data_quality"] == {
        "status": "warning",
        "warnings": [
            (
                "Latest quarterly financial periods "
                "are not aligned."
            )
        ],
    }


class FakeIncomeStatementNotFoundService:
    def __init__(
        self,
        db,
        provider,
    ):
        pass

    async def collect_income_statements(
        self,
        symbol,
    ):
        raise ValueError(
            "Asset not found for symbol: INVALID"
        )


def test_financial_collection_endpoint_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.financial_collection.IncomeStatementService",
        FakeIncomeStatementNotFoundService,
    )

    monkeypatch.setattr(
        "app.api.financial_collection.get_financial_data_provider",
        lambda: object(),
    )

    response = client.post(
        "/financials/collect/INVALID"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Asset not found for symbol: INVALID"
    )