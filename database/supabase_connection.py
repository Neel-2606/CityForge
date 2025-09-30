"""Supabase database connection and operations."""

import os
import asyncio
from typing import Optional, Dict, Any, List
import logging
from supabase import create_client, Client
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import json

logger = logging.getLogger(__name__)


class SupabaseManager:
    """Manages Supabase database operations."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.client: Optional[Client] = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to Supabase."""
        try:
            if not self.supabase_url or not self.supabase_key:
                logger.warning("Supabase credentials not found, using local storage")
                return False
            
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            # Test connection
            result = self.client.table('test').select("*").limit(1).execute()
            self.connected = True
            logger.info("✅ Connected to Supabase successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            self.connected = False
            return False
    
    async def init_tables(self):
        """Initialize required tables in Supabase."""
        if not self.connected:
            return False
        
        try:
            # Create tables using Supabase SQL
            tables_sql = [
                """
                CREATE TABLE IF NOT EXISTS wards (
                    id SERIAL PRIMARY KEY,
                    ward_name VARCHAR(100) NOT NULL,
                    ward_number INTEGER,
                    geometry GEOMETRY(POLYGON, 4326),
                    population INTEGER,
                    area_km2 FLOAT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS air_quality_data (
                    id SERIAL PRIMARY KEY,
                    ward_id INTEGER REFERENCES wards(id),
                    timestamp TIMESTAMP DEFAULT NOW(),
                    aqi FLOAT,
                    pm25 FLOAT,
                    pm10 FLOAT,
                    no2 FLOAT,
                    so2 FLOAT,
                    co FLOAT,
                    geometry GEOMETRY(POINT, 4326)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS temperature_data (
                    id SERIAL PRIMARY KEY,
                    ward_id INTEGER REFERENCES wards(id),
                    timestamp TIMESTAMP DEFAULT NOW(),
                    temperature_celsius FLOAT,
                    heat_index FLOAT,
                    geometry GEOMETRY(POINT, 4326)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS vegetation_data (
                    id SERIAL PRIMARY KEY,
                    ward_id INTEGER REFERENCES wards(id),
                    timestamp TIMESTAMP DEFAULT NOW(),
                    ndvi FLOAT,
                    green_cover_percent FLOAT,
                    geometry GEOMETRY(POINT, 4326)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS flood_risk_data (
                    id SERIAL PRIMARY KEY,
                    ward_id INTEGER REFERENCES wards(id),
                    timestamp TIMESTAMP DEFAULT NOW(),
                    precipitation_mm FLOAT,
                    flood_risk_score FLOAT,
                    drainage_capacity FLOAT,
                    geometry GEOMETRY(POINT, 4326)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS recommendations (
                    id SERIAL PRIMARY KEY,
                    ward_id INTEGER REFERENCES wards(id),
                    intervention_type VARCHAR(50),
                    title VARCHAR(200),
                    description TEXT,
                    priority VARCHAR(20),
                    estimated_cost FLOAT,
                    timeline_months INTEGER,
                    impact_score FLOAT,
                    population_affected INTEGER,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            ]
            
            for sql in tables_sql:
                self.client.rpc('execute_sql', {'sql': sql}).execute()
            
            logger.info("✅ Supabase tables initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase tables: {e}")
            return False
    
    async def store_ward_data(self, wards_gdf: gpd.GeoDataFrame):
        """Store ward boundary data."""
        if not self.connected:
            return False
        
        try:
            for idx, ward in wards_gdf.iterrows():
                data = {
                    'ward_name': ward.get('name', f'Ward {idx+1}'),
                    'ward_number': idx + 1,
                    'geometry': ward.geometry.wkt if hasattr(ward, 'geometry') else None,
                    'population': int(ward.get('population', 50000 + idx * 1000)),
                    'area_km2': float(ward.get('area', 10.5 + idx * 0.5))
                }
                
                self.client.table('wards').insert(data).execute()
            
            logger.info(f"✅ Stored {len(wards_gdf)} wards in Supabase")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store ward data: {e}")
            return False
    
    async def store_air_quality_data(self, data: List[Dict[str, Any]]):
        """Store air quality data."""
        if not self.connected:
            return False
        
        try:
            self.client.table('air_quality_data').insert(data).execute()
            logger.info(f"✅ Stored {len(data)} air quality records")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store air quality data: {e}")
            return False
    
    async def store_temperature_data(self, data: List[Dict[str, Any]]):
        """Store temperature data."""
        if not self.connected:
            return False
        
        try:
            self.client.table('temperature_data').insert(data).execute()
            logger.info(f"✅ Stored {len(data)} temperature records")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store temperature data: {e}")
            return False
    
    async def store_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Store recommendations."""
        if not self.connected:
            return False
        
        try:
            self.client.table('recommendations').insert(recommendations).execute()
            logger.info(f"✅ Stored {len(recommendations)} recommendations")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store recommendations: {e}")
            return False
    
    async def get_ward_data(self) -> Optional[List[Dict]]:
        """Retrieve ward data."""
        if not self.connected:
            return None
        
        try:
            result = self.client.table('wards').select("*").execute()
            return result.data
        except Exception as e:
            logger.error(f"❌ Failed to retrieve ward data: {e}")
            return None
    
    async def get_latest_air_quality(self) -> Optional[List[Dict]]:
        """Get latest air quality data."""
        if not self.connected:
            return None
        
        try:
            result = self.client.table('air_quality_data')\
                .select("*")\
                .order('timestamp', desc=True)\
                .limit(100)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"❌ Failed to retrieve air quality data: {e}")
            return None


class LocalStorageManager:
    """Fallback local storage when Supabase is not available."""
    
    def __init__(self):
        self.data_dir = "data/local_db"
        os.makedirs(self.data_dir, exist_ok=True)
        self.connected = True
    
    async def connect(self) -> bool:
        """Always returns True for local storage."""
        logger.info("✅ Using local file storage")
        return True
    
    async def init_tables(self):
        """Create directory structure."""
        directories = [
            "wards", "air_quality", "temperature", 
            "vegetation", "flood_risk", "recommendations"
        ]
        for dir_name in directories:
            os.makedirs(f"{self.data_dir}/{dir_name}", exist_ok=True)
        return True
    
    async def store_ward_data(self, wards_gdf: gpd.GeoDataFrame):
        """Store ward data as GeoJSON."""
        try:
            wards_gdf.to_file(f"{self.data_dir}/wards/wards.geojson", driver="GeoJSON")
            logger.info(f"✅ Stored {len(wards_gdf)} wards locally")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store ward data locally: {e}")
            return False
    
    async def store_air_quality_data(self, data: List[Dict[str, Any]]):
        """Store air quality data as JSON."""
        try:
            with open(f"{self.data_dir}/air_quality/latest.json", 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"✅ Stored {len(data)} air quality records locally")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store air quality data locally: {e}")
            return False
    
    async def store_temperature_data(self, data: List[Dict[str, Any]]):
        """Store temperature data as JSON."""
        try:
            with open(f"{self.data_dir}/temperature/latest.json", 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"✅ Stored {len(data)} temperature records locally")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store temperature data locally: {e}")
            return False
    
    async def store_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Store recommendations as JSON."""
        try:
            with open(f"{self.data_dir}/recommendations/latest.json", 'w') as f:
                json.dump(recommendations, f, indent=2, default=str)
            logger.info(f"✅ Stored {len(recommendations)} recommendations locally")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store recommendations locally: {e}")
            return False
    
    async def get_ward_data(self) -> Optional[List[Dict]]:
        """Retrieve ward data from local storage."""
        try:
            if os.path.exists(f"{self.data_dir}/wards/wards.geojson"):
                gdf = gpd.read_file(f"{self.data_dir}/wards/wards.geojson")
                return gdf.to_dict('records')
            return None
        except Exception as e:
            logger.error(f"❌ Failed to retrieve ward data locally: {e}")
            return None


# Global database manager
db_manager = None


async def get_db_manager():
    """Get database manager (Supabase or local fallback)."""
    global db_manager
    
    if db_manager is None:
        # Try Supabase first
        supabase_manager = SupabaseManager()
        if await supabase_manager.connect():
            db_manager = supabase_manager
            await db_manager.init_tables()
        else:
            # Fallback to local storage
            db_manager = LocalStorageManager()
            await db_manager.connect()
            await db_manager.init_tables()
    
    return db_manager
