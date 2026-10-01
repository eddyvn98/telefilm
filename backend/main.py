from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .core.config import get_settings
from .core.database import init_db
from .routers import admin, auth, catalog, history, media, stream
from .services.telegram_client import TelegramClientService

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    tg_service = TelegramClientService.get_instance()
    try:
        await tg_service.start()
        print("Telegram client started")
    except Exception as exc:
        print(f"Telegram client startup failed: {exc}")
    yield
    await tg_service.stop()


docs_enabled = bool(settings.ENABLE_API_DOCS)
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method.upper() not in {"GET", "HEAD", "OPTIONS"}:
        fetch_site = (request.headers.get("Sec-Fetch-Site") or "").lower()
        if fetch_site == "cross-site":
            return JSONResponse({"detail": "Cross-site request blocked"}, status_code=403)

        origin = request.headers.get("Origin")
        if origin:
            origin_host = (urlparse(origin).hostname or "").lower()
            forwarded_host = (request.headers.get("X-Forwarded-Host") or "").split(",")[0].strip()
            host_header = forwarded_host or request.headers.get("Host", "")
            request_host = host_header.rsplit(":", 1)[0].strip("[]").lower()
            if origin_host and request_host and origin_host != request_host:
                return JSONResponse({"detail": "Origin mismatch"}, status_code=403)

    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://telegram.org https://unpkg.com https://cdn.plyr.io; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.plyr.io https://cdnjs.cloudflare.com; "
        "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "media-src 'self' blob:; "
        "connect-src 'self' https://api.telegram.org; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'self' https://t.me https://*.t.me https://web.telegram.org https://*.telegram.org https://desktop.telegram.org"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    elif "Cache-Control" not in response.headers:
        response.headers["Cache-Control"] = "no-cache"
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]
    return response


# Only application code/styles are public static assets.
app.mount("/static/css", StaticFiles(directory="frontend/static/css"), name="static-css")
app.mount("/static/js", StaticFiles(directory="frontend/static/js"), name="static-js")

templates = Jinja2Templates(directory="frontend/templates")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin")
def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
app.include_router(stream.router, prefix="/api/stream", tags=["stream"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(media.router, prefix="/static", tags=["media"])
