import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import conversations_router, synthesis_router, auth_router, documents_router, voice_router, messages_router
from services.scheduler import start_scheduler, stop_scheduler
from config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Voice-first, privacy-focused AI journaling companion",
    version="0.1.0",
)

# CORS from environment configuration
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(synthesis_router)
app.include_router(documents_router)
app.include_router(voice_router)
app.include_router(messages_router)


@app.on_event("startup")
def startup():
    try:
        init_db()
        logger.info("Database initialized successfully")
        start_scheduler()
        logger.info("Background scheduler started")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise


@app.on_event("shutdown")
def shutdown():
    stop_scheduler()
    logger.info("Background scheduler stopped")


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "modes": ["auto", "architect", "simulator", "scribe"],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
