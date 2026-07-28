from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.asset import AssetCreate, AssetResponse
from app.services.asset_service import (
    AssetAlreadyExistsError,
    AssetNotFoundError,
    AssetService,
)


router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
) -> AssetResponse:
    service = AssetService(db)

    try:
        return service.create_asset(asset_data)
    except AssetAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[AssetResponse],
)
def list_assets(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> list[AssetResponse]:
    service = AssetService(db)

    return service.list_assets(
        offset=offset,
        limit=limit,
        active_only=active_only,
    )


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
) -> AssetResponse:
    service = AssetService(db)

    try:
        return service.get_asset(asset_id)
    except AssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc