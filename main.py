"""Main FastAPI application for Urban Resilience Dashboard."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from config import settings
from api.routes import layers, recommendations, health
from database.supabase_connection import get_db_manager
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    try:
        db_manager = await get_db_manager()
        logger.info("✅ Database connection established")
        print("🚀 Urban Resilience Dashboard Backend Started")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        print("⚠️  Continuing without database connection")
        print("🚀 Urban Resilience Dashboard Backend Started")
    yield
    # Shutdown
    print("👋 Shutting down Urban Resilience Dashboard Backend")


# Create FastAPI application
app = FastAPI(
    title="Urban Resilience Dashboard API",
    description="Backend API for NASA Space Apps Challenge 2025 - Mumbai Urban Resilience Dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(layers.router, prefix="/layers", tags=["Map Layers"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Urban Resilience Dashboard API",
        "version": "1.0.0",
        "city": "Mumbai, India",
        "hackathon": "NASA International Space Apps Challenge 2025"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
