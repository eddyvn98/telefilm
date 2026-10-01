import mimetypes

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from ..core.config import get_settings
from ..core.database import AsyncSessionLocal
from ..core.limits import ConcurrencyLimiter, SlidingWindowLimiter
from ..core.models import Movie
from ..core.security import create_stream_token, session_user, validate_stream_token
from ..services.telegram_client import TelegramClientService

router = APIRouter()
settings = get_settings()
token_limiter = SlidingWindowLimiter(settings.STREAM_TOKEN_RATE_PER_MINUTE)
request_limiter = SlidingWindowLimiter(settings.STREAM_REQUEST_RATE_PER_MINUTE)
stream_limiter = ConcurrencyLimiter(settings.MAX_CONCURRENT_STREAMS_PER_USER)


@router.get("/{movie_id}/token")
async def issue_stream_token(
    movie_id: int,
    user: dict = Depends(session_user),
):
    user_id = str(user["id"])
    await token_limiter.check(user_id)
    async with AsyncSessionLocal() as db:
        exists = await db.scalar(select(Movie.id).where(Movie.id == movie_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {
        "token": create_stream_token(movie_id, user_id, str(user["_session_id"])),
        "expires_in": max(300, min(int(settings.STREAM_TOKEN_TTL_SECONDS), 60 * 60 * 12)),
    }


@router.get("/{movie_id}")
async def stream_video(
    movie_id: int,
    request: Request,
    range_header: str | None = Header(None, alias="Range"),
    token: str = Query(..., min_length=20, max_length=1024),
    user: dict = Depends(session_user),
):
    user_id = str(user["id"])
    session_id = str(user["_session_id"])
    validate_stream_token(token, movie_id, user_id, session_id)
    await request_limiter.check(user_id)

    async with AsyncSessionLocal() as db:
        movie = await db.scalar(select(Movie).where(Movie.id == movie_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    try:
        channel_str, message_str = movie.file_id.split(":", 1)
        channel_id = int(channel_str)
        message_id = int(message_str)
    except (AttributeError, ValueError):
        raise HTTPException(status_code=500, detail="Invalid media reference")

    client_service = TelegramClientService.get_instance()
    await client_service.start()
    message = await client_service.get_message(channel_id, message_id)
    if not message or not message.file:
        raise HTTPException(status_code=404, detail="File not found on Telegram")

    file_size = int(getattr(message.file, "size", 0) or 0)
    if file_size <= 0:
        raise HTTPException(status_code=404, detail="File size unavailable")

    status_code = 200
    start = 0
    end = file_size - 1
    if range_header:
        if "," in range_header:
            raise HTTPException(status_code=416, detail="Multiple ranges are not supported")
        try:
            unit, range_value = range_header.split("=", 1)
            if unit.strip().lower() != "bytes":
                raise ValueError
            start_raw, end_raw = range_value.split("-", 1)
            if not start_raw:
                raise ValueError
            start = int(start_raw)
            end = int(end_raw) if end_raw else end
            status_code = 206
        except (ValueError, TypeError):
            raise HTTPException(status_code=416, detail="Invalid Range header")

    if start < 0 or start >= file_size or end < start:
        raise HTTPException(status_code=416, detail="Range not satisfiable")
    end = min(end, file_size - 1)
    content_length = end - start + 1

    await stream_limiter.acquire(user_id)

    async def iterfile():
        try:
            async for chunk in client_service.get_file_stream(
                channel_id,
                message_id,
                offset=start,
                limit=content_length,
            ):
                if await request.is_disconnected():
                    break
                yield chunk
        finally:
            await stream_limiter.release(user_id)

    media_type = mimetypes.guess_type(movie.title or "")[0] or "application/octet-stream"
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Cache-Control": "no-store",
    }
    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    return StreamingResponse(
        iterfile(),
        status_code=status_code,
        headers=headers,
        media_type=media_type,
    )
