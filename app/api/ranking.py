from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.ranking import (
    RankingResponse,
    ScreenerResponse,
)
from app.services.ranking_service import (
    RankingService,
)


router = APIRouter(
    tags=["Ranking & Screener"],
)


@router.get(
    "/ranking",
    response_model=RankingResponse,
)
def get_ranking(
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
    min_confidence: Decimal = Query(
        default=Decimal("0"),
        ge=Decimal("0"),
        le=Decimal("1"),
    ),
    db: Session = Depends(get_db),
) -> RankingResponse:
    service = RankingService(
        db=db,
    )

    results, total = (
        service.get_ranking(
            offset=offset,
            limit=limit,
            min_confidence=(
                min_confidence
            ),
        )
    )

    return RankingResponse(
        total=total,
        count=len(results),
        offset=offset,
        limit=limit,
        results=results,
    )


@router.get(
    "/screener",
    response_model=ScreenerResponse,
)
def screen_assets(
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
    sector: str | None = None,
    market: str | None = None,
    country: str | None = None,
    asset_type: str | None = None,
    min_growth_score: Decimal | None = Query(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    ),
    min_quality_score: Decimal | None = Query(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    ),
    min_valuation_score: Decimal | None = Query(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    ),
    min_composite_score: Decimal | None = Query(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    ),
    min_confidence: Decimal | None = Query(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    ),
    alignment_ok: bool | None = None,
    db: Session = Depends(get_db),
) -> ScreenerResponse:
    service = RankingService(
        db=db,
    )

    results, total = service.screen(
        offset=offset,
        limit=limit,
        sector=sector,
        market=market,
        country=country,
        asset_type=asset_type,
        min_growth_score=(
            min_growth_score
        ),
        min_quality_score=(
            min_quality_score
        ),
        min_valuation_score=(
            min_valuation_score
        ),
        min_composite_score=(
            min_composite_score
        ),
        min_confidence=(
            min_confidence
        ),
        alignment_ok=alignment_ok,
    )

    return ScreenerResponse(
        total=total,
        count=len(results),
        offset=offset,
        limit=limit,
        results=results,
    )