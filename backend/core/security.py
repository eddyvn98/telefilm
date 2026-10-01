import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from .config import get_settings
from fastapi import Depends, Header, HTTPException

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

async def admin_user(user: dict = Depends(authorized_user)) -> dict:
    telegram_id = str(user.get("id"))
    admins = _csv_ids(settings.ADMIN_TELEGRAM_IDS)
    if not admins or telegram_id not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
