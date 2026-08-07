# AION V2

AION V2 is a FastAPI financial-analysis backend that collects market and company data, stores normalized financial statements, computes TTM metrics and scores, and exposes ranking, screener, watchlist, and refresh workflows.

## Architecture

```text
FastAPI API
    |
    +-- Assets / Refresh / Batch Refresh
    +-- Company / Market
    +-- Financial Statements
    +-- TTM / Metrics / Scores
    +-- Ranking / Screener / Watchlist
    +-- Health / System
    |
Service Layer
    |
    +-- Provider factories + fallback + retry/timeout telemetry
    +-- Repository layer
    |
PostgreSQL                 External providers
    |                       |
    +-- assets              +-- SEC EDGAR (financial income primary)
    +-- company_profiles    +-- Yahoo Finance (fallback / company / market)
    +-- market_prices
    +-- financial tables
    +-- watchlist_items

Redis
    +-- readiness dependency
    +-- optional API rate limiting
```

Financial period dates are canonicalized before persistence so providers that report slightly different fiscal period-end dates can still align for TTM calculations.

## Requirements

- Python 3.13+
- Docker Desktop or compatible Docker Engine
- PostgreSQL 17 (provided by Docker Compose)
- Redis 7 (provided by Docker Compose)

## Local setup

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a real SEC contact value:

```text
SEC_USER_AGENT=AION-V2 your-real-email@example.com
```

Never commit `.env`.

Start infrastructure and apply migrations:

```powershell
docker compose up -d
alembic upgrade head
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

Run tests:

```powershell
python -m pytest
```

## Provider policy

The default chains are configured in `.env`:

```text
COMPANY_PROVIDER_CHAIN=yahoo
MARKET_PROVIDER_CHAIN=yahoo
FINANCIAL_PROVIDER_CHAIN=sec,yahoo
```

SEC EDGAR is the primary income-statement source. Yahoo Finance is the fallback financial source and currently remains the source for balance-sheet and cash-flow collection. Provider retry/fallback activity is exposed in refresh responses under `provider_observability`.

Inspect effective provider configuration without exposing secrets:

```text
GET /system/providers
```

## Main workflows

Refresh one asset and include analysis:

```text
POST /assets/refresh/AAPL?include_analysis=true
```

Refresh many assets:

```text
POST /assets/refresh-batch
```

Check data recency:

```text
GET /assets/freshness/AAPL
```

Rank and screen stored assets:

```text
GET /ranking
GET /screener
```

Manage watchlist:

```text
POST   /watchlist/AAPL
GET    /watchlist
DELETE /watchlist/AAPL
```

## Scheduled refresh

AION does not run an in-process scheduler. This avoids duplicate schedules when the API is deployed with multiple workers. Use cron, Windows Task Scheduler, CI, or an orchestration platform to invoke the refresh CLI.

Refresh watchlist assets:

```powershell
python -m app.jobs.refresh_assets --scope watchlist --include-analysis --concurrency 3
```

Refresh all active assets:

```powershell
python -m app.jobs.refresh_assets --scope active --include-analysis --concurrency 3
```

## Production hardening

Every HTTP response includes `X-Request-ID`. Access/provider logs are structured JSON. Optional Redis-backed rate limiting can be enabled with:

```text
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=120
```

Health endpoints:

```text
GET /health
GET /health/database
GET /health/readiness
```

`/health/readiness` returns HTTP 503 when PostgreSQL or Redis is unavailable.

## Product v1

Authenticated product endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `/watchlist` is user-scoped and requires a Bearer token.
- `/portfolios` provides user-owned portfolios and positions with latest-price valuation when market data exists.

Before production deployment, set a long random `AUTH_SECRET_KEY` and run `alembic upgrade head`.
