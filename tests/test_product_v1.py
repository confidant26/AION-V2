from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.security import decode_access_token, hash_password, verify_password
from app.main import app
from app.models.asset import Asset
from app.schemas.auth import UserLoginRequest, UserRegisterRequest
from app.schemas.portfolio import PortfolioCreate, PortfolioPositionUpsert
from app.services.auth_service import AuthService, AuthenticationError, UserAlreadyExistsError
from app.services.portfolio_service import PortfolioNotFoundError, PortfolioService


client = TestClient(app)


def test_password_hash_round_trip():
    encoded = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)
    assert "correct horse" not in encoded


def test_auth_register_login_and_token(db_session):
    service = AuthService(db_session)
    user = service.register(UserRegisterRequest(email=" User@Example.com ", password="strong-pass-123", display_name=" User "))
    assert user.email == "user@example.com"
    token = service.login(UserLoginRequest(email="user@example.com", password="strong-pass-123"))
    payload = decode_access_token(token.access_token)
    assert int(payload["sub"]) == user.id


def test_auth_duplicate_and_bad_password(db_session):
    service = AuthService(db_session)
    request = UserRegisterRequest(email="user@example.com", password="strong-pass-123")
    service.register(request)
    with pytest.raises(UserAlreadyExistsError):
        service.register(request)
    with pytest.raises(AuthenticationError):
        service.login(UserLoginRequest(email="user@example.com", password="wrong"))


def test_portfolio_is_user_scoped(db_session):
    auth = AuthService(db_session)
    u1 = auth.register(UserRegisterRequest(email="one@example.com", password="strong-pass-123"))
    u2 = auth.register(UserRegisterRequest(email="two@example.com", password="strong-pass-123"))
    p1 = PortfolioService(db_session, user_id=u1.id).create(PortfolioCreate(name="Core"))
    assert [p.name for p in PortfolioService(db_session, user_id=u1.id).list()] == ["Core"]
    assert PortfolioService(db_session, user_id=u2.id).list() == []
    with pytest.raises(PortfolioNotFoundError):
        PortfolioService(db_session, user_id=u2.id).get(p1.id)


def test_portfolio_position_valuation(db_session):
    auth = AuthService(db_session)
    user = auth.register(UserRegisterRequest(email="investor@example.com", password="strong-pass-123"))
    asset = Asset(symbol="AAPL", name="Apple Inc.", asset_type="stock", currency="USD")
    db_session.add(asset); db_session.commit(); db_session.refresh(asset)
    service = PortfolioService(db_session, user_id=user.id)
    portfolio = service.create(PortfolioCreate(name="Long Term"))
    detail = service.upsert_position(
        portfolio_id=portfolio.id,
        symbol="AAPL",
        data=PortfolioPositionUpsert(quantity=Decimal("2"), average_cost=Decimal("100"), currency="USD"),
    )
    assert detail.position_count == 1
    assert detail.positions[0].cost_basis == Decimal("200")
    assert detail.positions[0].market_value is None


def test_auth_me_requires_bearer_token():
    app.dependency_overrides.pop(get_current_user, None)
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_portfolio_api_uses_authenticated_user(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7, email="user@example.com", active=True)
    class FakePortfolioService:
        def __init__(self, db, *, user_id): assert user_id == 7
        def list(self): return []
    monkeypatch.setattr("app.api.portfolio.PortfolioService", FakePortfolioService)
    response = client.get("/portfolios")
    assert response.status_code == 200
    assert response.json() == []
    app.dependency_overrides.pop(get_current_user, None)
