from typing import Any

from pydantic import BaseModel, Field, field_validator


class AssetBatchRefreshRequest(BaseModel):
    symbols: list[str] = Field(
        min_length=1,
        max_length=50,
    )

    include_analysis: bool = False

    concurrency: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for value in values:
            symbol = value.strip().upper()

            if not symbol:
                continue

            if symbol in seen:
                continue

            seen.add(symbol)
            normalized.append(symbol)

        if not normalized:
            raise ValueError(
                "At least one valid symbol is required."
            )

        return normalized


class AssetBatchRefreshItem(BaseModel):
    symbol: str
    success: bool

    result: dict[str, Any] | None = None
    error: str | None = None


class AssetBatchRefreshResponse(BaseModel):
    requested_count: int
    success_count: int
    failed_count: int

    results: list[AssetBatchRefreshItem] = Field(
        default_factory=list,
    )