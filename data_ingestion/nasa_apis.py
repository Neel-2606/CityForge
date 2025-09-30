"""NASA API data ingestion modules."""

import asyncio
import aiohttp
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import xarray as xr
from config import settings
import logging

# Import real NASA implementation
from .real_nasa_apis import RealNASADataOrchestrator, RealMODISLSTIngester, RealAuraOMIIngester

logger = logging.getLogger(__name__)


class NASAEarthdataClient:
    """Client for NASA Earthdata APIs."""
    
    def __init__(self):
        self.base_url = "https://cmr.earthdata.nasa.gov/search"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_granules(self, collection_id: str, temporal: str, 
                            spatial: Dict[str, float]) -> List[Dict]:
        """Search for data granules."""
        params = {
            "collection_concept_id": collection_id,
            "temporal": temporal,
            "bounding_box": f"{spatial['west']},{spatial['south']},{spatial['east']},{spatial['north']}",
            "page_size": 100,
            "format": "json"
        }
        
        async with self.session.get(f"{self.base_url}/granules", params=params) as response:
            data = await response.json()
            return data.get("feed", {}).get("entry", [])


class MODISLSTIngester:
    """MODIS Land Surface Temperature data ingestion."""
    
    def __init__(self):
        self.collection_id = "C61MOTA1NRTLST"  # MODIS Terra LST
        
    async def fetch_lst_data(self, date_range: Tuple[str, str]) -> Optional[xr.Dataset]:
        """Fetch MODIS LST data for Mumbai region."""
        try:
            # This is a simplified implementation
            # In production, use NASA's actual data access APIs
            
            mumbai_bounds = settings.mumbai_bounds
            
            # Create synthetic data for demo (replace with actual API calls)
            lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 50)
            lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 50)
            
            # Generate realistic temperature data (25-40°C range)
            base_temp = 30.0
            temp_data = base_temp + np.random.normal(0, 5, (len(lats), len(lons)))
            temp_data = np.clip(temp_data, 25, 45)
            
            dataset = xr.Dataset({
                "LST_Day": (["lat", "lon"], temp_data),
                "LST_Night": (["lat", "lon"], temp_data - 5)
            }, coords={
                "lat": lats,
                "lon": lons,
                "time": datetime.now()
            })
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error fetching MODIS LST data: {e}")
            return None


class AuraOMIIngester:
    """Aura OMI air quality data ingestion."""
    
    def __init__(self):
        self.collection_id = "C1443528505-LAADS"  # OMI NO2
        
    async def fetch_air_quality_data(self, date_range: Tuple[str, str]) -> Optional[xr.Dataset]:
        """Fetch Aura OMI air quality data."""
        try:
            mumbai_bounds = settings.mumbai_bounds
            
            # Create synthetic air quality data for demo
            lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 30)
            lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 30)
            
            # Generate realistic NO2 and SO2 data
            no2_data = np.random.lognormal(mean=3.0, sigma=0.5, size=(len(lats), len(lons)))
            so2_data = np.random.lognormal(mean=2.0, sigma=0.3, size=(len(lats), len(lons)))
            
            dataset = xr.Dataset({
                "NO2_column": (["lat", "lon"], no2_data),
                "SO2_column": (["lat", "lon"], so2_data),
                "aerosol_index": (["lat", "lon"], np.random.uniform(0, 3, (len(lats), len(lons))))
            }, coords={
                "lat": lats,
                "lon": lons,
                "time": datetime.now()
            })
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error fetching Aura OMI data: {e}")
            return None


class GPMPrecipitationIngester:
    """GPM precipitation data ingestion."""
    
    def __init__(self):
        self.collection_id = "C1598621093-GES_DISC"  # GPM IMERG
        
    async def fetch_precipitation_data(self, date_range: Tuple[str, str]) -> Optional[xr.Dataset]:
        """Fetch GPM precipitation data."""
        try:
            mumbai_bounds = settings.mumbai_bounds
            
            # Create synthetic precipitation data
            lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 40)
            lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 40)
            
            # Generate monsoon-influenced precipitation data
            precip_data = np.random.exponential(scale=5.0, size=(len(lats), len(lons)))
            
            dataset = xr.Dataset({
                "precipitation": (["lat", "lon"], precip_data),
                "precipitation_error": (["lat", "lon"], precip_data * 0.1)
            }, coords={
                "lat": lats,
                "lon": lons,
                "time": datetime.now()
            })
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error fetching GPM data: {e}")
            return None


class LandsatNDVIIngester:
    """Landsat NDVI data ingestion."""
    
    def __init__(self):
        self.collection_id = "C2021957295-LPCLOUD"  # Landsat 8 Collection 2
        
    async def fetch_ndvi_data(self, date_range: Tuple[str, str]) -> Optional[xr.Dataset]:
        """Fetch Landsat NDVI data."""
        try:
            mumbai_bounds = settings.mumbai_bounds
            
            # Create synthetic NDVI data
            lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 60)
            lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 60)
            
            # Generate realistic NDVI data (-1 to 1, with urban areas having lower values)
            base_ndvi = np.random.uniform(-0.2, 0.8, (len(lats), len(lons)))
            
            # Simulate urban areas with lower NDVI
            urban_mask = np.random.random((len(lats), len(lons))) < 0.6
            base_ndvi[urban_mask] = np.random.uniform(-0.1, 0.3, np.sum(urban_mask))
            
            dataset = xr.Dataset({
                "NDVI": (["lat", "lon"], base_ndvi),
                "EVI": (["lat", "lon"], base_ndvi * 0.8),
                "land_cover": (["lat", "lon"], np.random.randint(1, 8, (len(lats), len(lons))))
            }, coords={
                "lat": lats,
                "lon": lons,
                "time": datetime.now()
            })
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error fetching Landsat NDVI data: {e}")
            return None


class VIIRSNightLightsIngester:
    """VIIRS Night Lights data ingestion."""
    
    async def fetch_nightlights_data(self, date_range: Tuple[str, str]) -> Optional[xr.Dataset]:
        """Fetch VIIRS night lights data."""
        try:
            mumbai_bounds = settings.mumbai_bounds
            
            # Create synthetic night lights data
            lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 50)
            lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 50)
            
            # Generate realistic night lights data (higher in urban centers)
            lights_data = np.random.lognormal(mean=2.0, sigma=1.0, size=(len(lats), len(lons)))
            
            dataset = xr.Dataset({
                "DNB_radiance": (["lat", "lon"], lights_data),
                "quality_flag": (["lat", "lon"], np.random.randint(0, 4, (len(lats), len(lons))))
            }, coords={
                "lat": lats,
                "lon": lons,
                "time": datetime.now()
            })
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error fetching VIIRS data: {e}")
            return None


# Use the real NASA data orchestrator for production
NASADataOrchestrator = RealNASADataOrchestrator

# Keep legacy classes for backward compatibility
class LegacyNASADataOrchestrator:
    """Legacy orchestrator - kept for backward compatibility."""
    
    def __init__(self):
        # Use real ingesters now
        self.modis_ingester = RealMODISLSTIngester()
        self.omi_ingester = RealAuraOMIIngester()
        self.gpm_ingester = GPMPrecipitationIngester()
        self.landsat_ingester = LandsatNDVIIngester()
        self.viirs_ingester = VIIRSNightLightsIngester()
        
    async def ingest_all_data(self, days_back: int = 7) -> Dict[str, xr.Dataset]:
        """Ingest data from all NASA sources with real API calls where possible."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_range = (start_date.isoformat(), end_date.isoformat())
        
        logger.info(f"🛰️  Starting NASA data ingestion for date range: {date_range}")
        
        # Check if we have real NASA credentials
        has_real_creds = (settings.NASA_EARTHDATA_USERNAME and 
                         settings.NASA_EARTHDATA_USERNAME != "demo_user")
        
        if has_real_creds:
            logger.info("🔑 Using real NASA Earthdata credentials")
        else:
            logger.info("🎭 Using synthetic data (no real credentials)")
        
        # Run all ingestion tasks concurrently
        tasks = [
            self.modis_ingester.fetch_lst_data(date_range),
            self.omi_ingester.fetch_air_quality_data(date_range),
            self.gpm_ingester.fetch_precipitation_data(date_range),
            self.landsat_ingester.fetch_ndvi_data(date_range),
            self.viirs_ingester.fetch_nightlights_data(date_range)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        datasets = {}
        source_names = ["modis_lst", "aura_omi", "gpm_precip", "landsat_ndvi", "viirs_lights"]
        
        for i, (source, result) in enumerate(zip(source_names, results)):
            if isinstance(result, Exception):
                logger.error(f"❌ Failed to ingest {source}: {result}")
            elif result is not None:
                datasets[source] = result
                logger.info(f"✅ Successfully ingested {source} data")
        
        return datasets
    
    async def save_datasets(self, datasets: Dict[str, xr.Dataset]) -> None:
        """Save datasets to local storage."""
        import os
        os.makedirs("data/processed", exist_ok=True)
        
        for source, dataset in datasets.items():
            try:
                output_path = f"data/processed/{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.nc"
                dataset.to_netcdf(output_path)
                logger.info(f"💾 Saved {source} data to {output_path}")
            except Exception as e:
                logger.error(f"❌ Failed to save {source} data: {e}")
