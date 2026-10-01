import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from .config import get_settings
from fastapi import Header, HTTPException, Request

settings = get_settings()

def _csv_ids(value: str) -> set[str]:
    return {item.strip() for item in (value or "").split(",") if item.strip()}

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

async def authorized_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data")
) -> dict:
    user_data = validate_telegram_data(x_telegram_init_data)
    telegram_id = str(user_data.get("id"))
    allowed = _csv_ids(settings.ALLOWED_TELEGRAM_IDS)
    if telegram_id not in allowed:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return user_data

async def admin_user(
    request: Request,
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
) -> dict:
    # Local desktop admin remains usable. Cloudflare Tunnel requests carry
    # forwarding headers, so they must still authenticate through Telegram.
    client_host = request.client.host if request.client else ""
    forwarded = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For")
    )
    if not forwarded and client_host in {"127.0.0.1", "::1", "localhost"}:
        return {"id": "local-admin", "local": True}

    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Telegram authentication required")
    user = validate_telegram_data(x_telegram_init_data)
    telegram_id = str(user.get("id"))
    allowed = _csv_ids(settings.ALLOWED_TELEGRAM_IDS)
    admins = _csv_ids(settings.ADMIN_TELEGRAM_IDS)
    if telegram_id not in allowed or telegram_id not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def create_stream_token(movie_id: int, user_id: str) -> str:
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    expires = int(time.time()) + max(300, min(int(settings.STREAM_TOKEN_TTL_SECONDS), 60 * 60 * 12))
    payload = f"{int(movie_id)}:{str(user_id)}:{expires}"
    signature = hmac.new(settings.BOT_TOKEN.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"

def validate_stream_token(token: str, movie_id: int) -> dict:
    try:
        token_movie, user_id, expires_raw, signature = str(token or "").rsplit(":", 3)
        expires = int(expires_raw)
        token_movie_id = int(token_movie)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid stream token")
    if token_movie_id != int(movie_id) or expires < int(time.time()):
        raise HTTPException(status_code=401, detail="Expired or invalid stream token")
    if expires > int(time.time()) + (60 * 60 * 12) + 60:
        raise HTTPException(status_code=401, detail="Invalid stream token lifetime")
    payload = f"{token_movie_id}:{user_id}:{expires}"
    expected = hmac.new(settings.BOT_TOKEN.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid stream token")
    return {"user_id": user_id, "expires": expires}
