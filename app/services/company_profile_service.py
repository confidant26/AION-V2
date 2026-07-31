from sqlalchemy.orm import Session

from app.mappers.company_profile import map_company_profile_create_to_model
from app.providers.company.base import CompanyDataProvider
from app.repositories.asset_repository import AssetRepository
from app.repositories.company_profile_repository import (
    CompanyProfileRepository,
)
from app.schemas.company_profile import CompanyProfileCreate


class CompanyProfileService:
    def __init__(
        self,
        db: Session,
        provider: CompanyDataProvider,
    ):
        self.asset_repository = AssetRepository(db)
        self.company_profile_repository = CompanyProfileRepository(db)
        self.provider = provider

    async def collect_company_profile(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(clean_symbol)

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        raw_profile = await self.provider.get_company_profile(
            clean_symbol
        )

        profile_data = CompanyProfileCreate(
            company_name=raw_profile["company_name"],
            sector=raw_profile.get("sector"),
            industry=raw_profile.get("industry"),
            country=raw_profile.get("country"),
            currency=raw_profile.get("currency"),
            market_cap=raw_profile.get("market_cap"),
            full_time_employees=raw_profile.get(
                "full_time_employees"
            ),
            website=raw_profile.get("website"),
            description=raw_profile.get("description"),
        )

        existing_profile = (
            self.company_profile_repository.get_by_asset_id(
                asset.id
            )
        )

        if existing_profile is None:
            company_profile = map_company_profile_create_to_model(
                data=profile_data,
                asset_id=asset.id,
            )

            return self.company_profile_repository.create(
                company_profile
            )

        existing_profile.company_name = profile_data.company_name
        existing_profile.sector = profile_data.sector
        existing_profile.industry = profile_data.industry
        existing_profile.country = profile_data.country
        existing_profile.currency = profile_data.currency
        existing_profile.market_cap = profile_data.market_cap
        existing_profile.full_time_employees = (
            profile_data.full_time_employees
        )
        existing_profile.website = profile_data.website
        existing_profile.description = profile_data.description

        return self.company_profile_repository.update(
            existing_profile
        )

    def get_company_profile(
        self,
        symbol: str,
    ):
        clean_symbol = symbol.strip().upper()

        asset = self.asset_repository.get_by_symbol(clean_symbol)

        if asset is None:
            raise ValueError(
                f"Asset not found for symbol: {clean_symbol}"
            )

        company_profile = (
            self.company_profile_repository.get_by_asset_id(
                asset.id
            )
        )

        if company_profile is None:
            raise ValueError(
                f"Company profile not found for symbol: {clean_symbol}"
            )

        return company_profile