"""Health check endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import psutil
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float


class SystemStatus(BaseModel):
    """System status response model."""
    database_connected: bool
    data_ingestion_status: str
    last_data_update: str
    active_processing_jobs: int


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    try:
        # Get system metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            uptime_seconds=psutil.boot_time(),
            memory_usage_mb=memory_info.used / (1024 * 1024),
            cpu_usage_percent=cpu_percent
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/status", response_model=SystemStatus)
async def system_status():
    """Detailed system status endpoint."""
    try:
        # In a real implementation, these would check actual system status
        return SystemStatus(
            database_connected=True,  # Would check actual DB connection
            data_ingestion_status="operational",
            last_data_update=datetime.now().isoformat(),
            active_processing_jobs=0
        )
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(status_code=500, detail="System status check failed")


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"message": "pong", "timestamp": datetime.now()}
