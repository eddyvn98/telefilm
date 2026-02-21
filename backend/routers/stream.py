from fastapi import APIRouter, Header, HTTPException, Request, Response, Query
from fastapi.responses import StreamingResponse
from ..services.telegram_client import TelegramClientService
from ..core.database import get_db, AsyncSession
from ..core.models import Movie
from ..core.security import validate_telegram_data, get_settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

router = APIRouter()

@router.get("/{movie_id}")
async def stream_video(
    movie_id: int, 
    request: Request,
    range: str = Header(None),
    init_data: str = Query(..., alias="init_data"),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream video content. Supports Range requests for seeking.
    """
    # Authorization check
    settings = get_settings()
    user_data = validate_telegram_data(init_data)
    telegram_id = str(user_data.get("id"))
    
    if settings.ALLOWED_TELEGRAM_IDS:
        allowed_list = [i.strip() for i in settings.ALLOWED_TELEGRAM_IDS.split(",") if i.strip()]
        if telegram_id not in allowed_list:
            raise HTTPException(status_code=403, detail="Unauthorized")

    # 1. Get Movie Metadata
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
    
    file_size = await client_service.get_file_size(channel_id, message_id)
    if file_size == 0:
         raise HTTPException(status_code=404, detail="File not found on Telegram")

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
        except ValueError:
            pass # Fallback to full file if invalid range
            
    # Ensure end is within bounds
    if end >= file_size:
        end = file_size - 1
        
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
    }

    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        headers["Content-Length"] = str(content_length)
    
    return StreamingResponse(
        iterfile(),
        status_code=status_code,
        headers=headers,
        media_type="video/mp4"
    )
