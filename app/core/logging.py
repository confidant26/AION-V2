from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings


_request_id: ContextVar[str | None] = ContextVar(
    "aion_request_id",
    default=None,
)


def set_request_id(
    value: str,
) -> Token:
    return _request_id.set(value)


def reset_request_id(
    token: Token,
) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()

        if request_id:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def configure_logging() -> None:
    level_name = settings.log_level.strip().upper()
    level = getattr(
        logging,
        level_name,
        logging.INFO,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if getattr(
        root_logger,
        "_aion_configured",
        False,
    ):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger._aion_configured = True
