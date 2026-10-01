from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from ..core.paths import resolve_media_file
from ..core.security import session_user

router = APIRouter()


async def _serve(kind: str, filename: str, user: dict):
    path = resolve_media_file(kind, filename)
    return FileResponse(
        path,
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.get("/thumbnails/{filename:path}")
async def thumbnail(filename: str, user: dict = Depends(session_user)):
    return await _serve("thumbnails", filename, user)


@router.get("/backdrops/{filename:path}")
async def backdrop(filename: str, user: dict = Depends(session_user)):
    return await _serve("backdrops", filename, user)
