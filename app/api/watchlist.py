from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.watchlist import (
    WatchlistDeleteResponse,
    WatchlistItemResponse,
    WatchlistResponse,
)
from app.services.watchlist_service import (
    WatchlistAlreadyExistsError,
    WatchlistAssetNotFoundError,
    WatchlistItemNotFoundError,
    WatchlistService,
)


router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"],
)


@router.post(
    "/{symbol}",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
) -> WatchlistItemResponse:
    service = WatchlistService(
        db=db,
    )

    try:
        return service.add(
            symbol
        )

    except WatchlistAssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except WatchlistAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=WatchlistResponse,
)
def list_watchlist(
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    service = WatchlistService(
        db=db,
    )

    items = service.list_items()

    return WatchlistResponse(
        count=len(items),
        results=items,
    )


@router.get(
    "/{symbol}",
    response_model=WatchlistItemResponse,
)
def get_watchlist_item(
    symbol: str,
    db: Session = Depends(get_db),
) -> WatchlistItemResponse:
    service = WatchlistService(
        db=db,
    )

    try:
        return service.get(
            symbol
        )

    except WatchlistItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{symbol}",
    response_model=WatchlistDeleteResponse,
)
def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
) -> WatchlistDeleteResponse:
    service = WatchlistService(
        db=db,
    )

    try:
        clean_symbol = service.remove(
            symbol
        )

        return WatchlistDeleteResponse(
            message=(
                "Asset removed from watchlist."
            ),
            symbol=clean_symbol,
        )

    except WatchlistItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc