from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.routers import api_router
from app.routers.admin import admin_router
from app.routers.auth import limiter, me_router
from app.routers.certificates import router as certificates_router
from app.routers.media import router as media_router
from app.routers.verify import router as verify_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title="IAM Training Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter state attached to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(me_router, prefix="/api/v1")
app.include_router(admin_router)   # paths are already /api/v1/admin/...
app.include_router(certificates_router, prefix="/api/v1")
app.include_router(media_router)
app.include_router(verify_router)  # /verify/{uuid} — public, no /api/v1 prefix


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
