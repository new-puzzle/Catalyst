from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import conversations_router, synthesis_router
from .config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Voice-first, privacy-focused AI journaling companion",
    version="0.1.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations_router)
app.include_router(synthesis_router)


@app.on_event("startup")
def startup():
    init_db()


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
