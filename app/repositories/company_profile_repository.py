from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company_profile import CompanyProfile


class CompanyProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, company_profile: CompanyProfile) -> CompanyProfile:
        self.db.add(company_profile)
        self.db.commit()
        self.db.refresh(company_profile)

        return company_profile

    def get_by_asset_id(self, asset_id: int) -> CompanyProfile | None:
        statement = select(CompanyProfile).where(
            CompanyProfile.asset_id == asset_id
        )

        return self.db.scalar(statement)

    def update(
        self,
        company_profile: CompanyProfile,
    ) -> CompanyProfile:
        self.db.commit()
        self.db.refresh(company_profile)

        return company_profile