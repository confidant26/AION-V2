from app.models.company_profile import CompanyProfile
from app.schemas.company_profile import CompanyProfileCreate


def map_company_profile_create_to_model(
    data: CompanyProfileCreate,
    asset_id: int,
) -> CompanyProfile:
    return CompanyProfile(
        asset_id=asset_id,
        company_name=data.company_name,
        sector=data.sector,
        industry=data.industry,
        country=data.country,
        currency=data.currency,
        market_cap=data.market_cap,
        full_time_employees=data.full_time_employees,
        website=data.website,
        description=data.description,
    )