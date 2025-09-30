"""Startup script for Urban Resilience Dashboard backend."""

import asyncio
import sys
import os
from pathlib import Path
import logging
import uvicorn
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config import settings
from scripts.run_analysis import run_full_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print startup banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║            🏙️  URBAN RESILIENCE DASHBOARD BACKEND 🏙️             ║
    ║                                                                  ║
    ║              NASA International Space Apps Challenge 2025        ║
    ║              Theme: Data Pathways to Healthy Cities              ║
    ║              Focus City: Mumbai, India                           ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"🚀 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Host: {settings.api_host}:{settings.api_port}")
    print(f"🗄️  Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'Not configured'}")
    print(f"📁 Data Directory: {settings.data_dir}")
    print("=" * 70)


async def initialize_system():
    """Initialize the system with sample data."""
    logger.info("🔧 Initializing Urban Resilience Dashboard...")
    
    try:
        # Create necessary directories
        settings.data_dir.mkdir(exist_ok=True)
        settings.raw_data_dir.mkdir(exist_ok=True)
        settings.processed_data_dir.mkdir(exist_ok=True)
        settings.cache_dir.mkdir(exist_ok=True)
        
        logger.info("📁 Created data directories")
        
        # Check if we should run initial analysis
        if os.getenv("RUN_INITIAL_ANALYSIS", "false").lower() == "true":
            logger.info("🔍 Running initial analysis...")
            await run_full_analysis()
            logger.info("✅ Initial analysis completed")
        
        logger.info("🎯 System initialization completed successfully")
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {e}")
        raise


def start_api_server():
    """Start the FastAPI server."""
    logger.info("🚀 Starting FastAPI server...")
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
        access_log=settings.debug
    )


async def main():
    """Main startup function."""
    print_banner()
    
    try:
        # Initialize system
        await initialize_system()
        
        # Start API server
        start_api_server()
        
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"💥 Startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "analysis":
            # Run analysis only
            print("🔍 Running Urban Resilience Analysis...")
            asyncio.run(run_full_analysis())
        elif command == "worker":
            # Start background worker
            print("👷 Starting background data worker...")
            os.environ["WORKER_MODE"] = "true"
            from scripts.data_ingestion_worker import main as worker_main
            asyncio.run(worker_main())
        elif command == "server":
            # Start server only (no initialization)
            print_banner()
            start_api_server()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: analysis, worker, server")
            sys.exit(1)
    else:
        # Default: full startup
        asyncio.run(main())
