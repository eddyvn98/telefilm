from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_db
from ..core.models import User
from ..core.limits import SlidingWindowLimiter
from ..core.security import create_session_token, validate_telegram_data

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()
login_limiter = SlidingWindowLimiter(30)


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    init_data: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    client_key = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For")
        or (request.client.host if request.client else "unknown")
    )
    await login_limiter.check(client_key.split(",")[0].strip())
    user_payload = validate_telegram_data(init_data)
    telegram_id = str(user_payload.get("id"))
    allowed = {item.strip() for item in settings.ALLOWED_TELEGRAM_IDS.split(",") if item.strip()}
    if telegram_id not in allowed:
        logger.warning("Access denied for Telegram ID %s", telegram_id)
        raise HTTPException(status_code=403, detail="Unauthorized")

    username = user_payload.get("username")
    first_name = user_payload.get("first_name")
    photo_url = user_payload.get("photo_url")

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            photo_url=photo_url,
            created_at=datetime.now(timezone.utc).isoformat(),
            is_admin=telegram_id in {
                item.strip() for item in settings.ADMIN_TELEGRAM_IDS.split(",") if item.strip()
            },
        )
        db.add(user)
    else:
        user.username = username
        user.first_name = first_name
        user.photo_url = photo_url
        user.is_admin = telegram_id in {
            item.strip() for item in settings.ADMIN_TELEGRAM_IDS.split(",") if item.strip()
        }

    await db.commit()
    await db.refresh(user)

    session_token = create_session_token(telegram_id)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max(300, int(settings.SESSION_TTL_SECONDS)),
        httponly=True,
        secure=bool(settings.SESSION_COOKIE_SECURE),
        samesite="none" if settings.SESSION_COOKIE_SECURE else "lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "ok",
        "user": {"id": user.telegram_id, "name": user.first_name, "is_admin": user.is_admin},
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        secure=bool(settings.SESSION_COOKIE_SECURE),
        samesite="none" if settings.SESSION_COOKIE_SECURE else "lax",
    )
    return {"status": "ok"}
