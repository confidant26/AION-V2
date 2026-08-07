from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.redis import redis_is_ready
from app.db.session import engine


router = APIRouter(
    tags=["Health"],
)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }


@router.get("/health/database")
def database_health_check() -> JSONResponse:
    database_ok = False

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        database_ok = True

    except SQLAlchemyError:
        database_ok = False

    return JSONResponse(
        status_code=(
            200
            if database_ok
            else 503
        ),
        content={
            "status": (
                "healthy"
                if database_ok
                else "unhealthy"
            ),
            "database": (
                "connected"
                if database_ok
                else "disconnected"
            ),
        },
    )


@router.get("/health/readiness")
def readiness_check() -> JSONResponse:
    database_ok = False

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        database_ok = True

    except SQLAlchemyError:
        database_ok = False

    redis_ok = redis_is_ready()
    ready = database_ok and redis_ok

    return JSONResponse(
        status_code=(
            200
            if ready
            else 503
        ),
        content={
            "status": (
                "ready"
                if ready
                else "not_ready"
            ),
            "database": (
                "connected"
                if database_ok
                else "disconnected"
            ),
            "redis": (
                "connected"
                if redis_ok
                else "disconnected"
            ),
        },
    )
