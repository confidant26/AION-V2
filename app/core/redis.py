from functools import lru_cache

from redis import Redis

from app.core.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    return Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=1,
        socket_timeout=1,
        decode_responses=True,
    )


def redis_is_ready() -> bool:
    try:
        return bool(
            get_redis_client().ping()
        )
    except Exception:
        return False


def close_redis_client() -> None:
    if get_redis_client.cache_info().currsize == 0:
        return

    try:
        get_redis_client().close()
    finally:
        get_redis_client.cache_clear()
