from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import chat, models, memory, vault, modules
from app.services.ollama_service import ollama_service
from app.services.rag_service import rag_service
from app.db.database import init_db
from app.core.security import SecurityHeadersMiddleware

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ogcai.main")

# Ensure cache/charts directory exists for static mounting
CHARTS_DIR = settings.CACHE_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown procedures."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    settings.ensure_directories()
    
    # 1. Initialize SQLite Database & WAL Mode
    await init_db()
    
    # 2. Check Ollama Connectivity & Warmup Default Model
    health = await ollama_service.check_health()
    logger.info(f"Ollama Service Status: {health.get('status')} (Models: {health.get('models_count', 0)})")
    if health.get("status") == "healthy":
        await ollama_service.warmup_models([settings.DEFAULT_MODEL])
    
    # 3. Check / Auto-Index Vault documents
    vault_status = rag_service.index_vault_directory()
    logger.info(f"ChromaDB Vault Initialized: {vault_status.get('total_vectors_in_db', 0)} vectors in database")
    
    yield
    
    # Graceful Shutdown
    logger.info("Shutting down OGCAI Core Engine...")
    await ollama_service.close()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="OGCAI Core Engine - Personal Local AI Assistant Backend with Auto-Model Switching, SQLite WAL Memory, 150GB+ ChromaDB Knowledge Vault & Specialized Everyday Modules",
    lifespan=lifespan
)

# Hardened Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration for Frontend Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Charts Directory
app.mount("/api/cache/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

# Include Routers
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(memory.router)
app.include_router(vault.router)
app.include_router(modules.router)

# Mount Frontend Build directory if available
FRONTEND_DIST = settings.STORAGE_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "ready",
            "endpoints": {
                "health": "/api/health",
                "models": "/api/models",
                "chat_stream": "/api/chat/stream",
                "conversations": "/api/conversations",
                "profile": "/api/profile",
                "starred": "/api/starred",
                "vault": "/api/vault/files"
            }
        }
