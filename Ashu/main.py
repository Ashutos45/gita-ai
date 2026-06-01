# main.py

import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from Ashu.database import engine, Base, check_and_run_migrations
import Ashu.models  # Required for table registration

from Ashu.auth import router as auth_router
from Ashu.routers.chat import router as chat_router
from Ashu.routers.voice import router as voice_router
from Ashu.routers.wellness import router as wellness_router
from Ashu.routers.abhyasa import router as abhyasa_router
from Ashu.routers.websocket import router as websocket_router
from Ashu.routers.health import router as health_router
from Ashu.routers.dashboard import router as dashboard_router

# Path to frontend folder (sibling of Ashu/)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


# =====================================
# Environment
# =====================================

ENVIRONMENT = os.getenv("ENV", "development")


# =====================================
# FastAPI App
# =====================================

app = FastAPI(
    title="GitaAI Backend",
    version="1.0.0",
    description="AI-powered Bhagavad Gita Guidance System",
    docs_url="/docs",
    redoc_url="/redoc"
)


# =====================================
# Create Tables
# =====================================

try:
    print("ATTEMPTING DB CONNECTION...")
    Base.metadata.create_all(bind=engine)
    check_and_run_migrations()
    print("POSTGRES CONNECTED SUCCESSFULLY")
except Exception as e:
    print(f"CRITICAL DATABASE STARTUP ERROR: {e}")

print("HEALTH ENDPOINT READY")


# =====================================
# CORS & Rate Limiting Middleware
# =====================================

import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 60, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exclude static assets and health checks from rate limiting
        path = request.url.path
        if path.startswith("/app") or path in ["/", "/health"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Keep only requests within window
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window]
        
        if len(self.requests[client_ip]) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down and reflect on your path."}
            )
            
        self.requests[client_ip].append(now)
        return await call_next(request)

# Register rate limiter
app.add_middleware(RateLimitMiddleware, limit=60, window=60)

if ENVIRONMENT == "development":
    allowed_origins = ["*"]
else:
    origins_env = os.getenv("ALLOWED_ORIGINS")
    if origins_env:
        allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    else:
        allowed_origins = ["https://yourfrontend.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================
# Include Routers
# =====================================

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(wellness_router)
app.include_router(abhyasa_router)
app.include_router(websocket_router)
app.include_router(health_router)
app.include_router(dashboard_router)


# =====================================
# Root Endpoint
# =====================================

@app.get("/")
def root():
    return RedirectResponse(url="/app/chat.html")


# =====================================
# Real Health Check
# =====================================

@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status
    }


# =====================================
# Serve Frontend (MUST be last)
# =====================================
# Mount frontend at /app so API routes are not shadowed.
# Access pages at: http://localhost:8000/app/chat.html
import os as _os
_frontend = _os.path.normpath(FRONTEND_DIR)
if _os.path.isdir(_frontend):
    app.mount("/app", StaticFiles(directory=_frontend, html=True), name="frontend")