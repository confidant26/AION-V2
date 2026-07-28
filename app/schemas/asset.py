from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    ETF = "etf"
    INDEX = "index"
    COMMODITY = "commodity"
    FOREX = "forex"
    BOND = "bond"
    FUND = "fund"


class AssetCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    asset_type: AssetType

    exchange: str | None = Field(default=None, max_length=64)
    market: str | None = Field(default=None, max_length=64)
    currency: str | None = Field(default=None, max_length=16)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    sector: str | None = Field(default=None, max_length=128)
    industry: str | None = Field(default=None, max_length=128)
    isin: str | None = Field(default=None, min_length=12, max_length=12)
    active: bool = True

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        normalized_value = value.strip().upper()

        if not normalized_value:
            raise ValueError("Symbol boş olamaz.")

        return normalized_value

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("Varlık adı boş olamaz.")

        return normalized_value

    @field_validator("exchange", "market", "currency", "country", "isin")
    @classmethod
    def normalize_uppercase_optional(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip().upper()

        return normalized_value or None

    @field_validator("sector", "industry")
    @classmethod
    def normalize_text_optional(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        return normalized_value or None


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    asset_type: AssetType

    exchange: str | None
    market: str | None
    currency: str | None
    country: str | None
    sector: str | None
    industry: str | None
    isin: str | None

    active: bool
    created_at: datetime
    updated_at: datetime