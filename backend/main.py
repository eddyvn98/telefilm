from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import get_settings
from .core.database import init_db
from .routers import auth, catalog, stream, admin
from .services.telegram_client import TelegramClientService

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    tg_service = TelegramClientService.get_instance()
    try:
        await tg_service.start()
        print("✅ Telegram Client Started")
    except Exception as e:
        print(f"❌ Telegram Client failed: {e}")
        
    yield
    
    # Shutdown
    await tg_service.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS (Allow everything for development/Web App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Allow being embedded in Telegram (Mobile and Web)
    response.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://t.me https://*.t.me https://web.telegram.org https://*.telegram.org https://desktop.telegram.org"
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Remove X-Frame-Options if it exists to not conflict with CSP
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]
    return response

# Mount Static Files (Frontend)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Templates
from fastapi.templating import Jinja2Templates
from fastapi import Request
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin")
def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
app.include_router(stream.router, prefix="/api/stream", tags=["stream"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
