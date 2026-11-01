from __future__ import annotations

import time
from collections import defaultdict
from typing import Annotated, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, Depends, HTTPException, Request, Response, status
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import get_settings
from app.db import get_db

SESSION_COOKIE = "vj_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14
LOGIN_WINDOW_S = 300
LOGIN_MAX_ATTEMPTS = 10

_ph = PasswordHasher()
_login_attempts: dict[str, list[float]] = defaultdict(list)


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().session_secret, salt="voice-journal-session")


def hash_passcode(passcode: str) -> str:
    return _ph.hash(passcode)


def verify_passcode(passcode: str, passcode_hash: str) -> bool:
    if not passcode_hash:
        return True
    try:
        return _ph.verify(passcode_hash, passcode)
    except VerifyMismatchError:
        return False


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_rate_limit(request: Request) -> None:
    key = _client_key(request)
    now = time.time()
    window = _login_attempts[key]
    _login_attempts[key] = [t for t in window if now - t < LOGIN_WINDOW_S]
    if len(_login_attempts[key]) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")


def record_failed_login(request: Request) -> None:
    _login_attempts[_client_key(request)].append(time.time())


def create_session(response: Response) -> None:
    token = _serializer().dumps({"auth": True})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        secure=True,
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def _session_valid(session: Optional[str]) -> bool:
    if session is None:
        return False
    try:
        data = _serializer().loads(session, max_age=SESSION_MAX_AGE)
        return bool(data.get("auth"))
    except BadSignature:
        return False


def effective_passcode_hash() -> str:
    cfg = get_settings()
    if cfg.passcode_hash:
        return cfg.passcode_hash
    try:
        with get_db() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = 'passcode_hash'").fetchone()
            return row["value"] if row else ""
    except Exception:
        return ""


async def require_auth(
    request: Request,
    vj_session: Annotated[Optional[str], Cookie(alias=SESSION_COOKIE)] = None,
) -> None:
    if not effective_passcode_hash():
        return
    if not _session_valid(vj_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


AuthDep = Annotated[None, Depends(require_auth)]
