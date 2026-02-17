import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from .config import get_settings
from fastapi import HTTPException, status

settings = get_settings()

def validate_telegram_data(init_data: str) -> dict:
    """
    Validates the initData string from Telegram WebApp.
    Returns the parsed user data as a dict if valid, raises HTTPException otherwise.
    """
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")

    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    if "hash" not in parsed_data:
        raise HTTPException(status_code=400, detail="Missing hash in initData")

    start_hash = parsed_data.pop("hash")
    
    # Check auth_date for replay attacks (e.g. 24 hours expiry)
    auth_date = int(parsed_data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise HTTPException(status_code=401, detail="Data is outdated")

    # Sort keys alphabetically
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    
    # Calculate HMAC
    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculations = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculations != start_hash:
        raise HTTPException(status_code=403, detail="Invalid data signature")

    # Parse user data
    user_data = json.loads(parsed_data.get("user", "{}"))
    return user_data
