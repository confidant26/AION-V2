from __future__ import annotations

from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os

import jwt
from jwt import InvalidTokenError

from app.core.config import settings


PASSWORD_ITERATIONS = 600_000
PASSWORD_SCHEME = "pbkdf2_sha256"


class InvalidCredentialsError(Exception):
    pass


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )

    return "$".join(
        [
            PASSWORD_SCHEME,
            str(PASSWORD_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(derived).decode("ascii"),
        ]
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations_raw, salt_raw, digest_raw = encoded.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_raw.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_raw.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def create_access_token(*, user_id: int, email: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.auth_access_token_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": expires_at,
        "iss": settings.auth_issuer,
        "type": "access",
    }
    token = jwt.encode(
        payload,
        settings.auth_secret_key,
        algorithm=settings.auth_algorithm,
    )
    return token, expires_at


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
            issuer=settings.auth_issuer,
        )
    except InvalidTokenError as exc:
        raise InvalidCredentialsError("Invalid or expired access token.") from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise InvalidCredentialsError("Invalid access token.")

    return payload
