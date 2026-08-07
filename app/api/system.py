from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/providers")
def provider_configuration() -> dict:
    return {
        "company": (
            settings
            .get_company_provider_names()
        ),
        "market": (
            settings
            .get_market_provider_names()
        ),
        "financial": (
            settings
            .get_financial_provider_names()
        ),
        "sec_configured": bool(
            settings.sec_user_agent.strip()
        ),
        "provider_policy": {
            "timeout_seconds": (
                settings
                .provider_timeout_seconds
            ),
            "max_attempts": (
                settings
                .provider_max_attempts
            ),
            "retry_delay_seconds": (
                settings
                .provider_retry_delay_seconds
            ),
        },
        "rate_limit": {
            "enabled": (
                settings
                .rate_limit_enabled
            ),
            "requests_per_minute": (
                settings
                .rate_limit_requests_per_minute
            ),
        },
    }
