from pydantic import BaseModel
from pydantic import ConfigDict


class CompanyProfileCreate(BaseModel):
    company_name: str
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    currency: str | None = None
    market_cap: int | None = None
    full_time_employees: int | None = None
    website: str | None = None
    description: str | None = None


class CompanyProfileResponse(CompanyProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int