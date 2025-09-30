"""External API data ingestion (WorldPop, OSM, etc.)."""

import asyncio
import aiohttp
import requests
from typing import Dict, List, Optional
import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd
from config import settings
import logging

logger = logging.getLogger(__name__)


class WorldPopIngester:
    """WorldPop population data ingestion."""
    
    def __init__(self):
        self.base_url = "https://www.worldpop.org/rest/data"
        
    async def fetch_population_data(self, country: str = "IND", year: int = 2020) -> Optional[gpd.GeoDataFrame]:
        """Fetch WorldPop population data for Mumbai."""
        try:
            # For demo purposes, create synthetic population data
            mumbai_bounds = settings.mumbai_bounds
            
            # Generate grid points
            import numpy as np
            lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 100)
            lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 100)
            
            points = []
            populations = []
            
            for lat in lats:
                for lon in lons:
                    points.append(Point(lon, lat))
                    # Higher population density in central areas
                    center_lat, center_lon = 19.0760, 72.8777  # Mumbai center
                    distance_from_center = ((lat - center_lat)**2 + (lon - center_lon)**2)**0.5
                    pop_density = max(0, 10000 * np.exp(-distance_from_center * 50))
                    populations.append(int(pop_density + np.random.normal(0, pop_density * 0.1)))
            
            gdf = gpd.GeoDataFrame({
                'population': populations,
                'geometry': points
            }, crs='EPSG:4326')
            
            return gdf
            
        except Exception as e:
            logger.error(f"Error fetching WorldPop data: {e}")
            return None


class OSMIngester:
    """OpenStreetMap data ingestion."""
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        
    async def fetch_healthcare_facilities(self) -> Optional[gpd.GeoDataFrame]:
        """Fetch healthcare facilities from OSM."""
        try:
            mumbai_bounds = settings.mumbai_bounds
            
            # Overpass query for healthcare facilities
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"~"^(hospital|clinic|doctors|pharmacy)$"]
                  ({mumbai_bounds["south"]},{mumbai_bounds["west"]},
                   {mumbai_bounds["north"]},{mumbai_bounds["east"]});
              way["amenity"~"^(hospital|clinic|doctors|pharmacy)$"]
                  ({mumbai_bounds["south"]},{mumbai_bounds["west"]},
                   {mumbai_bounds["north"]},{mumbai_bounds["east"]});
            );
            out center;
            """
            
            # For demo, create synthetic healthcare data
            import numpy as np
            np.random.seed(42)
            
            facilities = []
            facility_types = ['hospital', 'clinic', 'pharmacy', 'doctors']
            
            for i in range(50):  # 50 facilities
                lat = np.random.uniform(mumbai_bounds["south"], mumbai_bounds["north"])
                lon = np.random.uniform(mumbai_bounds["west"], mumbai_bounds["east"])
                facility_type = np.random.choice(facility_types)
                
                facilities.append({
                    'name': f'{facility_type.title()} {i+1}',
                    'amenity': facility_type,
                    'geometry': Point(lon, lat),
                    'osm_id': f'demo_{i}',
                    'capacity_beds': np.random.randint(10, 200) if facility_type == 'hospital' else None
                })
            
            gdf = gpd.GeoDataFrame(facilities, crs='EPSG:4326')
            return gdf
            
        except Exception as e:
            logger.error(f"Error fetching OSM healthcare data: {e}")
            return None
    
    async def fetch_green_spaces(self) -> Optional[gpd.GeoDataFrame]:
        """Fetch parks and green spaces from OSM."""
        try:
            mumbai_bounds = settings.mumbai_bounds
            
            # For demo, create synthetic green space data
            import numpy as np
            np.random.seed(43)
            
            green_spaces = []
            leisure_types = ['park', 'garden', 'playground', 'recreation_ground']
            
            for i in range(30):  # 30 green spaces
                # Create random polygons for parks
                center_lat = np.random.uniform(mumbai_bounds["south"], mumbai_bounds["north"])
                center_lon = np.random.uniform(mumbai_bounds["west"], mumbai_bounds["east"])
                
                # Create a small polygon around the center
                size = np.random.uniform(0.001, 0.005)  # Small parks
                coords = [
                    (center_lon - size, center_lat - size),
                    (center_lon + size, center_lat - size),
                    (center_lon + size, center_lat + size),
                    (center_lon - size, center_lat + size),
                    (center_lon - size, center_lat - size)
                ]
                
                leisure_type = np.random.choice(leisure_types)
                area_sqm = (size * 111000) ** 2  # Rough conversion to square meters
                
                green_spaces.append({
                    'name': f'{leisure_type.replace("_", " ").title()} {i+1}',
                    'leisure': leisure_type,
                    'geometry': Polygon(coords),
                    'osm_id': f'demo_green_{i}',
                    'area_sqm': area_sqm
                })
            
            gdf = gpd.GeoDataFrame(green_spaces, crs='EPSG:4326')
            return gdf
            
        except Exception as e:
            logger.error(f"Error fetching OSM green spaces data: {e}")
            return None


class MumbaiWardIngester:
    """Mumbai ward boundary data ingestion."""
    
    async def fetch_ward_boundaries(self) -> Optional[gpd.GeoDataFrame]:
        """Fetch Mumbai ward boundaries."""
        try:
            # For demo, create synthetic ward boundaries
            import numpy as np
            from shapely.geometry import Polygon
            
            mumbai_bounds = settings.mumbai_bounds
            wards = []
            
            # Create a 6x4 grid of wards (24 wards total)
            lat_step = (mumbai_bounds["north"] - mumbai_bounds["south"]) / 4
            lon_step = (mumbai_bounds["east"] - mumbai_bounds["west"]) / 6
            
            ward_number = 1
            for i in range(4):
                for j in range(6):
                    south = mumbai_bounds["south"] + i * lat_step
                    north = mumbai_bounds["south"] + (i + 1) * lat_step
                    west = mumbai_bounds["west"] + j * lon_step
                    east = mumbai_bounds["west"] + (j + 1) * lon_step
                    
                    coords = [
                        (west, south),
                        (east, south),
                        (east, north),
                        (west, north),
                        (west, south)
                    ]
                    
                    # Calculate area in sq km
                    area_sqkm = ((east - west) * 111) * ((north - south) * 111)
                    
                    # Estimate population based on area and density
                    population = int(area_sqkm * np.random.uniform(5000, 25000))
                    
                    wards.append({
                        'ward_number': ward_number,
                        'ward_name': f'Ward {ward_number}',
                        'geometry': Polygon(coords),
                        'population': population,
                        'area_sqkm': area_sqkm
                    })
                    
                    ward_number += 1
            
            gdf = gpd.GeoDataFrame(wards, crs='EPSG:4326')
            return gdf
            
        except Exception as e:
            logger.error(f"Error creating ward boundaries: {e}")
            return None


class CPCBIngester:
    """Central Pollution Control Board data ingestion."""
    
    async def fetch_pollution_data(self) -> Optional[pd.DataFrame]:
        """Fetch real-time pollution data from CPCB."""
        try:
            # For demo, create synthetic CPCB station data
            import numpy as np
            np.random.seed(44)
            
            stations = [
                {'name': 'Bandra', 'lat': 19.0596, 'lon': 72.8295},
                {'name': 'Andheri', 'lat': 19.1136, 'lon': 72.8697},
                {'name': 'Borivali', 'lat': 19.2307, 'lon': 72.8567},
                {'name': 'Colaba', 'lat': 18.9067, 'lon': 72.8147},
                {'name': 'Worli', 'lat': 19.0176, 'lon': 72.8162}
            ]
            
            pollution_data = []
            
            for station in stations:
                # Generate realistic pollution values
                pm25 = np.random.uniform(30, 150)  # µg/m³
                pm10 = pm25 * np.random.uniform(1.2, 2.0)
                no2 = np.random.uniform(20, 80)
                so2 = np.random.uniform(5, 30)
                
                # Calculate AQI (simplified)
                aqi = max(pm25 * 2, pm10 * 1.5, no2 * 2, so2 * 3)
                
                if aqi <= 50:
                    category = "Good"
                elif aqi <= 100:
                    category = "Moderate"
                elif aqi <= 200:
                    category = "Poor"
                else:
                    category = "Severe"
                
                pollution_data.append({
                    'station_name': station['name'],
                    'latitude': station['lat'],
                    'longitude': station['lon'],
                    'pm25': pm25,
                    'pm10': pm10,
                    'no2': no2,
                    'so2': so2,
                    'aqi': int(aqi),
                    'category': category,
                    'timestamp': pd.Timestamp.now()
                })
            
            return pd.DataFrame(pollution_data)
            
        except Exception as e:
            logger.error(f"Error fetching CPCB data: {e}")
            return None


class ExternalDataOrchestrator:
    """Orchestrates external data ingestion."""
    
    def __init__(self):
        self.worldpop_ingester = WorldPopIngester()
        self.osm_ingester = OSMIngester()
        self.ward_ingester = MumbaiWardIngester()
        self.cpcb_ingester = CPCBIngester()
    
    async def ingest_all_external_data(self) -> Dict[str, gpd.GeoDataFrame]:
        """Ingest all external data sources."""
        logger.info("Starting external data ingestion")
        
        # Run all ingestion tasks concurrently
        tasks = [
            self.worldpop_ingester.fetch_population_data(),
            self.osm_ingester.fetch_healthcare_facilities(),
            self.osm_ingester.fetch_green_spaces(),
            self.ward_ingester.fetch_ward_boundaries(),
            self.cpcb_ingester.fetch_pollution_data()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        datasets = {}
        source_names = ["worldpop", "healthcare", "green_spaces", "wards", "cpcb_pollution"]
        
        for source, result in zip(source_names, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to ingest {source}: {result}")
            elif result is not None:
                datasets[source] = result
                logger.info(f"Successfully ingested {source} data")
        
        return datasets
    
    async def save_datasets(self, datasets: Dict[str, gpd.GeoDataFrame]) -> None:
        """Save datasets to local storage."""
        for source, dataset in datasets.items():
            try:
                if hasattr(dataset, 'to_file'):  # GeoDataFrame
                    output_path = settings.raw_data_dir / f"{source}_data.geojson"
                    dataset.to_file(output_path, driver='GeoJSON')
                else:  # Regular DataFrame
                    output_path = settings.raw_data_dir / f"{source}_data.csv"
                    dataset.to_csv(output_path, index=False)
                
                logger.info(f"Saved {source} data to {output_path}")
            except Exception as e:
                logger.error(f"Failed to save {source} data: {e}")
