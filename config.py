"""Configuration settings for Urban Resilience Dashboard backend."""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://username:password@localhost:5432/urban_resilience"
    
    # NASA API Configuration
    NASA_EARTHDATA_USERNAME: Optional[str] = Field(default=None, env="NASA_EARTHDATA_USERNAME")
    NASA_EARTHDATA_PASSWORD: Optional[str] = Field(default=None, env="NASA_EARTHDATA_PASSWORD")
    NASA_EARTHDATA_TOKEN: Optional[str] = Field(default=None, env="NASA_EARTHDATA_TOKEN")
    google_earth_engine_service_account_key: Optional[str] = Field(default=None, env="GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT_KEY")
    
    # Supabase Configuration
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, env="SUPABASE_ANON_KEY")
    supabase_service_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")
    
    # External APIs
    worldpop_api_key: Optional[str] = Field(default=None, env="WORLDPOP_API_KEY")
    copernicus_api_key: Optional[str] = Field(default=None, env="COPERNICUS_API_KEY")
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_bucket_name: str = "urban-resilience-data"
    aws_region: str = "us-east-1"
    
    # Data Paths
    data_dir: Path = Path("data")
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"
    cache_dir: Path = data_dir / "cache"
    
    # Mumbai Specific Configuration
    mumbai_bounds: dict = {
        "north": 19.3,
        "south": 18.8,
        "east": 72.9,
        "west": 72.7
    }
    
    # Processing Configuration
    target_resolution: int = 500  # meters
    max_workers: int = 4
    cache_ttl: int = 3600  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Create data directories
for directory in [settings.data_dir, settings.raw_data_dir, 
                 settings.processed_data_dir, settings.cache_dir]:
    directory.mkdir(parents=True, exist_ok=True)
