from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.models import User
from ..core.security import validate_telegram_data
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
print("📌 Auth module loaded successfully", flush=True)

router = APIRouter()

@router.post("/login")
async def login(init_data: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    """
    Endpoint (accessible via POST) that accepts `initData` string.
    Validates it and creates/updates the user in DB.
    Returns the user object and a simple session token (mock for now, or just return user info).
    """
    from ..core.config import get_settings
    settings = get_settings()
    
    user_payload = validate_telegram_data(init_data)
    telegram_id = str(user_payload.get("id"))
    print(f"\n🔔 KẾT NỐI MỚI TỪ TELEGRAM ID: {telegram_id}\n", flush=True)
    logger.info(f"🔔 Login attempt from Telegram ID: {telegram_id}")

    # Whitelist check (Strict Mode)
    allowed_list = [i.strip() for i in settings.ALLOWED_TELEGRAM_IDS.split(",") if i.strip()]
    if telegram_id not in allowed_list:
        logger.warning(f"🚫 Access Denied for ID: {telegram_id}")
        raise HTTPException(status_code=403, detail="Unauthorized: You are not in the allowed list.")

    username = user_payload.get("username")
    first_name = user_payload.get("first_name")
    
    # Check if user exists
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            created_at=datetime.utcnow().isoformat(),
            is_admin=False 
        )
        db.add(user)
    else:
        # Update info if changed
        if user.username != username or user.first_name != first_name:
            user.username = username
            user.first_name = first_name
    
    await db.commit()
    await db.refresh(user)
    
    return {"status": "ok", "user": {"id": user.telegram_id, "name": user.first_name, "is_admin": user.is_admin}}
