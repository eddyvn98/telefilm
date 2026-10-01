from fastapi import APIRouter, Header, HTTPException, Request, Response, Query, Depends
from fastapi.responses import StreamingResponse
from ..services.telegram_client import TelegramClientService
from ..core.database import AsyncSessionLocal
from ..core.models import Movie
from ..core.security import validate_stream_token, authorized_user, create_stream_token, get_settings
from sqlalchemy import select

router = APIRouter()
settings = get_settings()

@router.get("/{movie_id}/token")
async def issue_stream_token(
    movie_id: int,
    user: dict = Depends(authorized_user),
):
    return {
        "token": create_stream_token(movie_id, str(user["id"])),
        "expires_in": max(30, min(int(settings.STREAM_TOKEN_TTL_SECONDS), 600)),
    }

@router.get("/{movie_id}")
async def stream_video(
    movie_id: int,
    request: Request,
    range: str = Header(None),
    token: str = Query(...),
):
    """
    Stream video content. Supports Range requests for seeking.
    A short-lived signed playback token is required; Telegram initData is never put in URLs.
    """
    validate_stream_token(token, movie_id)

    # 1. Get Movie Metadata
    # Avoid holding a DB session during long-lived StreamingResponse.
    # Query metadata first, then close the DB session before streaming.
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Movie).where(Movie.id == movie_id))
        movie = result.scalar_one_or_none()
    
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    print(f"DEBUG: Streaming movie {movie_id}, file_id: {movie.file_id}", flush=True)
    # file_id format expected: "channel_id:message_id" (e.g., "-100123456789:123")
    try:
        channel_str, msg_str = movie.file_id.split(":")
        channel_id = int(channel_str)
        message_id = int(msg_str)
        print(f"DEBUG: Parsed channel_id: {channel_id}, message_id: {message_id}", flush=True)
    except ValueError:
        print(f"ERROR: Invalid file_id format: {movie.file_id}", flush=True)
        raise HTTPException(status_code=500, detail="Invalid file_id format in DB")

    client_service = TelegramClientService.get_instance()
    await client_service.start() # Ensure started
    
    message = await client_service.get_message(channel_id, message_id)
    if not message or not message.file:
        raise HTTPException(status_code=404, detail="File not found on Telegram")
    file_size = int(getattr(message.file, "size", 0) or 0)
    if file_size <= 0:
        raise HTTPException(status_code=404, detail="File size unavailable")

    # 2. Parse Range Header
    status_code = 200
    start = 0
    end = file_size - 1
    
    if range:
        status_code = 206
        try:
            # Range: bytes=0-1023
            range_key, range_val = range.split("=")
            if range_key.strip() == "bytes":
                range_start, range_end = range_val.split("-")
                start = int(range_start)
                if range_end:
                    end = int(range_end)
        except (ValueError, TypeError):
            raise HTTPException(status_code=416, detail="Invalid Range header")

    if start < 0 or start >= file_size:
        raise HTTPException(status_code=416, detail="Range start out of bounds")
    if end >= file_size:
        end = file_size - 1
    if end < start:
        raise HTTPException(status_code=416, detail="Invalid Range header")

    content_length = end - start + 1
    
    # 3. Stream Generator
    async def iterfile():
        async for chunk in client_service.get_file_stream(
            channel_id, 
            message_id, 
            offset=start, 
            limit=content_length
        ):
            yield chunk

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": "video/mp4",
        "Content-Length": str(content_length),
    }

    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    
    return StreamingResponse(
        iterfile(),
        status_code=status_code,
        headers=headers,
        media_type="video/mp4"
    )
