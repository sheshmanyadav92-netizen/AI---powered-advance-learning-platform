"""Main FastAPI application entry point.
AI-Powered Personalized Learning Platform
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from .core.config import settings
from .core.logging_config import logger
from .models import Base, engine, SessionLocal
from .seeds.seed_data import seed_database
from .api.auth import router as auth_router, limiter
from .api.profile import router as profile_router
from .api.goal import router as goal_router
from .api.assessment import router as assessment_router
from .api.recommendations import router as recommendations_router
from .api.progress import router as progress_router
from .api.roles import router as roles_router
from .api.mentor import router as mentor_router
from .api.settings import router as settings_router
from .api.certificates import router as certificates_router
from .api.courses import router as courses_router

# Initialize database schema and seeds synchronously at startup
Base.metadata.create_all(bind=engine)
_db = SessionLocal()
try:
    seed_database(_db)
finally:
    _db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-agent adaptive learning platform with Bayesian Knowledge Tracing, ROI recommendation ranking, and OWASP ASVS security controls.",
)

# Attach SlowAPI limiter state
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please wait before retrying."}
    )

# Strict CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(goal_router)
app.include_router(assessment_router)
app.include_router(recommendations_router)
app.include_router(progress_router)
app.include_router(roles_router)
app.include_router(mentor_router)
app.include_router(settings_router)
app.include_router(certificates_router)
app.include_router(courses_router)

# Mount static files and frontend UI
base_dir = os.path.dirname(__file__)
dist_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "frontend", "dist"))
static_dir = os.path.join(base_dir, "static")

html_path = (
    os.path.join(dist_dir, "index.html")
    if (os.path.exists(dist_dir) and os.path.exists(os.path.join(dist_dir, "index.html")))
    else os.path.join(static_dir, "index.html")
)

if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    app.mount("/dist", StaticFiles(directory=dist_dir), name="dist_static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
def serve_frontend_ui():
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>AI-Powered Personalized Learning Platform</h1>")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/api")
def api_status():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "docs": "/docs",
        "version": settings.VERSION
    }
