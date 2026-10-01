import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, Request

from .config import get_settings

settings = get_settings()


def _csv_ids(value: str) -> set[str]:
    return {item.strip() for item in (value or "").split(",") if item.strip()}


def _signing_key() -> bytes:
    secret = (settings.SECRET_KEY or "").strip()
    weak_defaults = {"supersecretkey", "yoursupersecretkey", "changeme", "secret"}
    if len(secret) < 32 or secret.lower() in weak_defaults:
        secret = settings.BOT_TOKEN
    if not secret:
        raise HTTPException(status_code=500, detail="Server signing key is not configured")
    return secret.encode()


def _hmac(payload: str) -> str:
    return hmac.new(_signing_key(), payload.encode(), hashlib.sha256).hexdigest()


def validate_telegram_data(init_data: str) -> dict:
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")

    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    start_hash = parsed_data.pop("hash", "")
    if not start_hash:
        raise HTTPException(status_code=400, detail="Missing hash in initData")

    try:
        auth_date = int(parsed_data.get("auth_date", "0"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid auth_date")

    now = int(time.time())
    if auth_date <= 0 or auth_date > now + 60 or now - auth_date > 86400:
        raise HTTPException(status_code=401, detail="Data is outdated")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, start_hash):
        raise HTTPException(status_code=403, detail="Invalid data signature")

    try:
        user_data = json.loads(parsed_data.get("user", "{}"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid user payload")

    if not isinstance(user_data, dict) or not user_data.get("id"):
        raise HTTPException(status_code=400, detail="Missing Telegram user")
    return user_data


def _ensure_allowed(user_id: str) -> None:
    if user_id not in _csv_ids(settings.ALLOWED_TELEGRAM_IDS):
        raise HTTPException(status_code=403, detail="Unauthorized")


def create_session_token(user_id: str) -> str:
    expires = int(time.time()) + max(300, int(settings.SESSION_TTL_SECONDS))
    session_id = secrets.token_urlsafe(18)
    payload = f"{user_id}:{expires}:{session_id}"
    return f"{payload}:{_hmac(payload)}"


def validate_session_token(token: str) -> dict:
    try:
        user_id, expires_raw, session_id, signature = str(token or "").rsplit(":", 3)
        expires = int(expires_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid session")

    if not user_id or not session_id or expires < int(time.time()):
        raise HTTPException(status_code=401, detail="Session expired")

    max_expiry = int(time.time()) + max(300, int(settings.SESSION_TTL_SECONDS)) + 60
    if expires > max_expiry:
        raise HTTPException(status_code=401, detail="Invalid session lifetime")

    payload = f"{user_id}:{expires}:{session_id}"
    expected = _hmac(payload)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid session")

    _ensure_allowed(user_id)
    return {"id": user_id, "_session_id": session_id, "_session_expires": expires}


def _session_from_request(request: Request) -> dict:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    if not token:
        raise HTTPException(status_code=401, detail="Session required")
    return validate_session_token(token)


async def session_user(request: Request) -> dict:
    return _session_from_request(request)


async def authorized_user(request: Request) -> dict:
    return _session_from_request(request)


async def admin_user(request: Request) -> dict:
    client_host = request.client.host if request.client else ""
    request_host = (request.url.hostname or "").lower()
    forwarded = request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For")
    if (
        not forwarded
        and client_host in {"127.0.0.1", "::1", "localhost"}
        and request_host in {"127.0.0.1", "::1", "localhost"}
    ):
        return {"id": "local-admin", "local": True, "_session_id": "local"}

    user = _session_from_request(request)
    user_id = str(user.get("id"))
    admins = _csv_ids(settings.ADMIN_TELEGRAM_IDS)
    if not admins or user_id not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def create_stream_token(movie_id: int, user_id: str, session_id: str) -> str:
    expires = int(time.time()) + max(300, min(int(settings.STREAM_TOKEN_TTL_SECONDS), 60 * 60 * 12))
    nonce = secrets.token_urlsafe(8)
    payload = f"{int(movie_id)}:{user_id}:{session_id}:{expires}:{nonce}"
    return f"{payload}:{_hmac(payload)}"


def validate_stream_token(
    token: str,
    movie_id: int,
    expected_user_id: str,
    expected_session_id: str,
) -> dict:
    try:
        token_movie, user_id, session_id, expires_raw, nonce, signature = str(token or "").rsplit(":", 5)
        expires = int(expires_raw)
        token_movie_id = int(token_movie)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid stream token")

    now = int(time.time())
    if token_movie_id != int(movie_id) or expires < now:
        raise HTTPException(status_code=401, detail="Expired or invalid stream token")
    if expires > now + (60 * 60 * 12) + 60:
        raise HTTPException(status_code=401, detail="Invalid stream token lifetime")
    if user_id != str(expected_user_id) or session_id != str(expected_session_id):
        raise HTTPException(status_code=401, detail="Stream token is not valid for this session")

    payload = f"{token_movie_id}:{user_id}:{session_id}:{expires}:{nonce}"
    if not hmac.compare_digest(_hmac(payload), signature):
        raise HTTPException(status_code=401, detail="Invalid stream token")
    return {"user_id": user_id, "session_id": session_id, "expires": expires}
