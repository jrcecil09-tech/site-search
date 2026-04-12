"""
SiteDiligence API — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from routers import (
    auth,
    batch,
    billing,
    exports,
    integrations,
    mobile,
    projects,
    queries,
    storage,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "SiteDiligence backend API. "
        "Provides site diligence queries, GIS data, exports, and storage."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router,         prefix=f"{API_PREFIX}/auth",         tags=["auth"])
app.include_router(projects.router,     prefix=f"{API_PREFIX}/projects",     tags=["projects"])
app.include_router(queries.router,      prefix=f"{API_PREFIX}/queries",      tags=["queries"])
app.include_router(exports.router,      prefix=f"{API_PREFIX}/exports",      tags=["exports"])
app.include_router(storage.router,      prefix=f"{API_PREFIX}/storage",      tags=["storage"])
app.include_router(mobile.router,       prefix=f"{API_PREFIX}/mobile",       tags=["mobile"])
app.include_router(billing.router,      prefix=f"{API_PREFIX}/billing",      tags=["billing"])
app.include_router(integrations.router, prefix=f"{API_PREFIX}/integrations", tags=["integrations"])
app.include_router(batch.router,        prefix=f"{API_PREFIX}/batch",        tags=["batch"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "version": settings.app_version,
            "environment": settings.environment,
        },
    )


@app.get("/", tags=["system"])
async def root() -> JSONResponse:
    return JSONResponse(
        content={"message": f"{settings.app_name} v{settings.app_version}", "docs": "/docs"}
    )
