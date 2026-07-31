from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.providers.company.factory import get_company_data_provider
from app.services.company_profile_service import CompanyProfileService


router = APIRouter(
    prefix="/company",
    tags=["Company"],
)


@router.post("/collect/{symbol}")
async def collect_company_profile(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    provider = get_company_data_provider()

    service = CompanyProfileService(
        db=db,
        provider=provider,
    )

    try:
        company_profile = await service.collect_company_profile(
            symbol
        )

        return {
            "message": "Company profile collected successfully.",
            "id": company_profile.id,
            "asset_id": company_profile.asset_id,
            "symbol": symbol.strip().upper(),
            "company_name": company_profile.company_name,
            "sector": company_profile.sector,
            "industry": company_profile.industry,
            "country": company_profile.country,
            "currency": company_profile.currency,
            "market_cap": company_profile.market_cap,
            "full_time_employees": (
                company_profile.full_time_employees
            ),
            "website": company_profile.website,
            "description": company_profile.description,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/{symbol}")
def get_company_profile(
    symbol: str,
    db: Session = Depends(get_db),
) -> dict:
    provider = get_company_data_provider()

    service = CompanyProfileService(
        db=db,
        provider=provider,
    )

    try:
        company_profile = service.get_company_profile(
            symbol
        )

        return {
            "id": company_profile.id,
            "asset_id": company_profile.asset_id,
            "symbol": symbol.strip().upper(),
            "company_name": company_profile.company_name,
            "sector": company_profile.sector,
            "industry": company_profile.industry,
            "country": company_profile.country,
            "currency": company_profile.currency,
            "market_cap": company_profile.market_cap,
            "full_time_employees": (
                company_profile.full_time_employees
            ),
            "website": company_profile.website,
            "description": company_profile.description,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc