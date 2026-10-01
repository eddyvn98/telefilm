import os
from pathlib import Path
from fastapi import HTTPException
from .config import get_settings

settings = get_settings()
MEDIA_ROOT = Path("frontend/static").resolve()
MEDIA_DIRS = {
    "thumbnails": (MEDIA_ROOT / "thumbnails").resolve(),
    "backdrops": (MEDIA_ROOT / "backdrops").resolve(),
}


def _norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def allowed_upload_roots() -> list[str]:
    return [_norm(raw.strip()) for raw in (settings.UPLOAD_ROOTS or "").split(",") if raw.strip()]


def is_upload_path_allowed(path: str) -> bool:
    candidate = _norm(path)
    return any(candidate == root or candidate.startswith(root + os.sep) for root in allowed_upload_roots())


def validate_upload_path(path: str) -> str:
    if not path or not str(path).strip():
        raise HTTPException(status_code=400, detail="Path is required")
    candidate = _norm(str(path).strip())
    if not allowed_upload_roots():
        raise HTTPException(status_code=503, detail="UPLOAD_ROOTS is not configured")
    if not is_upload_path_allowed(candidate):
        raise HTTPException(status_code=403, detail="Path is outside allowed upload roots")
    if not os.path.exists(candidate):
        raise HTTPException(status_code=404, detail="Path not found")
    return candidate


def resolve_media_file(kind: str, filename: str) -> Path:
    root = MEDIA_DIRS.get(kind)
    if root is None:
        raise HTTPException(status_code=404, detail="Media type not found")
    candidate = (root / filename).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=404, detail="Media not found")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Media not found")
    return candidate


def resolve_media_url(url: str | None) -> Path | None:
    if not url:
        return None
    for kind in MEDIA_DIRS:
        prefix = f"/static/{kind}/"
        if url.startswith(prefix):
            filename = url[len(prefix):]
            try:
                return resolve_media_file(kind, filename)
            except HTTPException:
                return None
    return None
