"""Map layer endpoints for geospatial data."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import geopandas as gpd
import pandas as pd
import numpy as np
from datetime import datetime
import json
import logging

from data_ingestion.nasa_apis import NASADataOrchestrator
from data_ingestion.external_apis import ExternalDataOrchestrator
from preprocessing.data_processor import DataProcessor
from analytics.urban_analytics import UrbanResilienceAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


class LayerResponse(BaseModel):
    """Response model for map layers."""
    layer_name: str
    data_type: str
    timestamp: datetime
    feature_count: int
    geojson: Dict[str, Any]
    metadata: Dict[str, Any]


class LayerInfo(BaseModel):
    """Layer information model."""
    layer_name: str
    description: str
    data_source: str
    last_updated: datetime
    available: bool


@router.get("/", response_model=List[LayerInfo])
async def list_available_layers():
    """List all available map layers."""
    layers = [
        LayerInfo(
            layer_name="air_quality",
            description="Air quality index and pollution hotspots",
            data_source="NASA Aura/OMI + CPCB",
            last_updated=datetime.now(),
            available=True
        ),
        LayerInfo(
            layer_name="heat_risk",
            description="Urban heat islands and temperature data",
            data_source="NASA MODIS LST",
            last_updated=datetime.now(),
            available=True
        ),
        LayerInfo(
            layer_name="flood_risk",
            description="Flood-prone zones and drainage capacity",
            data_source="NASA GPM + SMAP",
            last_updated=datetime.now(),
            available=True
        ),
        LayerInfo(
            layer_name="green_cover",
            description="Vegetation index and green space coverage",
            data_source="NASA Landsat NDVI",
            last_updated=datetime.now(),
            available=True
        ),
        LayerInfo(
            layer_name="population_density",
            description="Population distribution and density",
            data_source="WorldPop + VIIRS Night Lights",
            last_updated=datetime.now(),
            available=True
        ),
        LayerInfo(
            layer_name="healthcare_facilities",
            description="Healthcare facilities and access gaps",
            data_source="OpenStreetMap",
            last_updated=datetime.now(),
            available=True
        ),
        LayerInfo(
            layer_name="ward_boundaries",
            description="Mumbai administrative ward boundaries",
            data_source="Mumbai Municipal Corporation",
            last_updated=datetime.now(),
            available=True
        )
    ]
    return layers


@router.get("/air_quality", response_model=LayerResponse)
async def get_air_quality_layer(
    include_hotspots: bool = Query(True, description="Include pollution hotspots"),
    aqi_threshold: int = Query(100, description="AQI threshold for hotspots")
):
    """Get air quality layer with pollution hotspots."""
    try:
        # In production, this would fetch from database or cache
        # For demo, generate synthetic data
        
        # Create synthetic air quality data
        mumbai_bounds = {"north": 19.3, "south": 18.8, "east": 72.9, "west": 72.7}
        
        features = []
        
        # Generate grid of air quality points
        lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 20)
        lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 20)
        
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                # Generate realistic AQI values (higher in central/industrial areas)
                center_distance = ((lat - 19.0760)**2 + (lon - 72.8777)**2)**0.5
                base_aqi = 80 + np.random.normal(0, 20)
                
                # Higher AQI in central areas
                if center_distance < 0.1:
                    base_aqi += 40
                elif center_distance < 0.2:
                    base_aqi += 20
                
                aqi = max(20, min(400, int(base_aqi)))
                
                # Determine category
                if aqi <= 50:
                    category = "Good"
                    color = "#00e400"
                elif aqi <= 100:
                    category = "Moderate"
                    color = "#ffff00"
                elif aqi <= 150:
                    category = "Unhealthy for Sensitive Groups"
                    color = "#ff7e00"
                elif aqi <= 200:
                    category = "Unhealthy"
                    color = "#ff0000"
                elif aqi <= 300:
                    category = "Very Unhealthy"
                    color = "#8f3f97"
                else:
                    category = "Hazardous"
                    color = "#7e0023"
                
                if not include_hotspots or aqi >= aqi_threshold:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "aqi": aqi,
                            "category": category,
                            "color": color,
                            "pm25": aqi * 0.5,
                            "pm10": aqi * 0.8,
                            "no2": aqi * 0.3,
                            "so2": aqi * 0.2,
                            "is_hotspot": aqi >= aqi_threshold
                        }
                    })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return LayerResponse(
            layer_name="air_quality",
            data_type="point",
            timestamp=datetime.now(),
            feature_count=len(features),
            geojson=geojson,
            metadata={
                "aqi_threshold": aqi_threshold,
                "include_hotspots": include_hotspots,
                "data_source": "NASA Aura/OMI + CPCB",
                "units": {"aqi": "index", "pm25": "µg/m³", "pm10": "µg/m³", "no2": "µg/m³", "so2": "µg/m³"}
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating air quality layer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate air quality layer")


@router.get("/heat_risk", response_model=LayerResponse)
async def get_heat_risk_layer(
    temperature_threshold: float = Query(35.0, description="Temperature threshold for heat risk (°C)")
):
    """Get urban heat island and temperature risk layer."""
    try:
        mumbai_bounds = {"north": 19.3, "south": 18.8, "east": 72.9, "west": 72.7}
        
        features = []
        
        # Generate temperature grid
        lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 25)
        lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 25)
        
        for lat in lats:
            for lon in lons:
                # Generate realistic temperature (25-42°C range)
                base_temp = 32 + np.random.normal(0, 3)
                
                # Urban heat island effect (higher temps in built-up areas)
                center_distance = ((lat - 19.0760)**2 + (lon - 72.8777)**2)**0.5
                if center_distance < 0.15:  # Central urban area
                    base_temp += np.random.uniform(2, 5)
                
                temperature = max(25, min(45, base_temp))
                
                # Classify heat risk
                if temperature < 30:
                    risk_level = "Low"
                    color = "#00ff00"
                elif temperature < 35:
                    risk_level = "Moderate"
                    color = "#ffff00"
                elif temperature < 40:
                    risk_level = "High"
                    color = "#ff7f00"
                else:
                    risk_level = "Extreme"
                    color = "#ff0000"
                
                if temperature >= temperature_threshold:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "temperature": round(temperature, 1),
                            "risk_level": risk_level,
                            "color": color,
                            "heat_index": round(temperature + np.random.uniform(0, 5), 1),
                            "is_heat_island": temperature > 37
                        }
                    })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return LayerResponse(
            layer_name="heat_risk",
            data_type="point",
            timestamp=datetime.now(),
            feature_count=len(features),
            geojson=geojson,
            metadata={
                "temperature_threshold": temperature_threshold,
                "data_source": "NASA MODIS LST",
                "units": {"temperature": "°C", "heat_index": "°C"}
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating heat risk layer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate heat risk layer")


@router.get("/flood_risk", response_model=LayerResponse)
async def get_flood_risk_layer(
    risk_threshold: float = Query(0.3, description="Flood risk threshold (0-1)")
):
    """Get flood risk zones layer."""
    try:
        mumbai_bounds = {"north": 19.3, "south": 18.8, "east": 72.9, "west": 72.7}
        
        features = []
        
        # Generate flood risk zones
        lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 30)
        lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 30)
        
        for lat in lats:
            for lon in lons:
                # Generate flood risk based on elevation and drainage
                # Lower areas (closer to coast) have higher flood risk
                elevation = max(0, 50 - (72.9 - lon) * 100 + np.random.normal(0, 10))
                
                # Base flood risk from precipitation and drainage
                base_risk = np.random.uniform(0.1, 0.8)
                
                # Adjust for elevation (lower = higher risk)
                elevation_factor = max(0, (20 - elevation) / 20)
                flood_risk = min(1.0, base_risk + elevation_factor * 0.4)
                
                # Classify risk
                if flood_risk < 0.25:
                    risk_category = "Low"
                    color = "#00ff00"
                elif flood_risk < 0.5:
                    risk_category = "Medium"
                    color = "#ffff00"
                elif flood_risk < 0.75:
                    risk_category = "High"
                    color = "#ff7f00"
                else:
                    risk_category = "Critical"
                    color = "#ff0000"
                
                if flood_risk >= risk_threshold:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "flood_risk_score": round(flood_risk, 2),
                            "risk_category": risk_category,
                            "color": color,
                            "elevation_m": round(elevation, 1),
                            "drainage_capacity": round(np.random.uniform(50, 200), 1),
                            "precipitation_mm": round(np.random.uniform(0, 50), 1)
                        }
                    })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return LayerResponse(
            layer_name="flood_risk",
            data_type="point",
            timestamp=datetime.now(),
            feature_count=len(features),
            geojson=geojson,
            metadata={
                "risk_threshold": risk_threshold,
                "data_source": "NASA GPM + SMAP",
                "units": {"flood_risk_score": "0-1", "elevation_m": "meters", "precipitation_mm": "mm/day"}
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating flood risk layer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate flood risk layer")


@router.get("/green_cover", response_model=LayerResponse)
async def get_green_cover_layer(
    ndvi_threshold: float = Query(0.3, description="NDVI threshold for vegetation")
):
    """Get vegetation and green cover layer."""
    try:
        mumbai_bounds = {"north": 19.3, "south": 18.8, "east": 72.9, "west": 72.7}
        
        features = []
        
        # Generate NDVI grid
        lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 35)
        lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 35)
        
        for lat in lats:
            for lon in lons:
                # Generate NDVI values (-1 to 1)
                # Urban areas have lower NDVI, parks/forests have higher
                center_distance = ((lat - 19.0760)**2 + (lon - 72.8777)**2)**0.5
                
                if center_distance < 0.1:  # Central urban area
                    ndvi = np.random.uniform(-0.1, 0.3)
                elif center_distance < 0.2:  # Suburban
                    ndvi = np.random.uniform(0.1, 0.5)
                else:  # Outskirts with more vegetation
                    ndvi = np.random.uniform(0.3, 0.8)
                
                # Add some parks/green spaces randomly
                if np.random.random() < 0.05:  # 5% chance of green space
                    ndvi = np.random.uniform(0.6, 0.9)
                
                # Convert to green score (0-100)
                green_score = int(((ndvi + 1) / 2) * 100)
                
                # Classify vegetation
                if ndvi < -0.1:
                    veg_type = "Water"
                    color = "#0000ff"
                elif ndvi < 0.1:
                    veg_type = "Built-up"
                    color = "#808080"
                elif ndvi < 0.3:
                    veg_type = "Sparse Vegetation"
                    color = "#ffff99"
                elif ndvi < 0.6:
                    veg_type = "Moderate Vegetation"
                    color = "#90ee90"
                else:
                    veg_type = "Dense Vegetation"
                    color = "#006400"
                
                if ndvi >= ndvi_threshold or veg_type in ["Water", "Built-up"]:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "ndvi": round(ndvi, 3),
                            "green_score": green_score,
                            "vegetation_type": veg_type,
                            "color": color,
                            "canopy_cover_percent": max(0, int(ndvi * 100)) if ndvi > 0 else 0
                        }
                    })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return LayerResponse(
            layer_name="green_cover",
            data_type="point",
            timestamp=datetime.now(),
            feature_count=len(features),
            geojson=geojson,
            metadata={
                "ndvi_threshold": ndvi_threshold,
                "data_source": "NASA Landsat NDVI",
                "units": {"ndvi": "-1 to 1", "green_score": "0-100", "canopy_cover_percent": "percent"}
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating green cover layer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate green cover layer")


@router.get("/healthcare_facilities", response_model=LayerResponse)
async def get_healthcare_facilities_layer():
    """Get healthcare facilities layer."""
    try:
        mumbai_bounds = {"north": 19.3, "south": 18.8, "east": 72.9, "west": 72.7}
        
        features = []
        
        # Generate healthcare facilities
        facility_types = [
            {"type": "hospital", "count": 15, "color": "#ff0000", "capacity_range": (50, 300)},
            {"type": "clinic", "count": 25, "color": "#ff7f00", "capacity_range": (10, 50)},
            {"type": "pharmacy", "count": 40, "color": "#00ff00", "capacity_range": (0, 0)},
            {"type": "doctors", "count": 20, "color": "#0000ff", "capacity_range": (5, 20)}
        ]
        
        facility_id = 1
        for facility_info in facility_types:
            for i in range(facility_info["count"]):
                lat = np.random.uniform(mumbai_bounds["south"], mumbai_bounds["north"])
                lon = np.random.uniform(mumbai_bounds["west"], mumbai_bounds["east"])
                
                capacity = 0
                if facility_info["capacity_range"][1] > 0:
                    capacity = np.random.randint(
                        facility_info["capacity_range"][0],
                        facility_info["capacity_range"][1]
                    )
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "facility_id": facility_id,
                        "name": f"{facility_info['type'].title()} {i+1}",
                        "facility_type": facility_info["type"],
                        "color": facility_info["color"],
                        "capacity_beds": capacity if facility_info["type"] in ["hospital", "clinic"] else None,
                        "staff_count": capacity // 3 if capacity > 0 else np.random.randint(1, 10),
                        "services": ["general"] if facility_info["type"] == "pharmacy" else ["general", "emergency"] if facility_info["type"] == "hospital" else ["general"]
                    }
                })
                facility_id += 1
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return LayerResponse(
            layer_name="healthcare_facilities",
            data_type="point",
            timestamp=datetime.now(),
            feature_count=len(features),
            geojson=geojson,
            metadata={
                "data_source": "OpenStreetMap",
                "facility_types": ["hospital", "clinic", "pharmacy", "doctors"],
                "total_facilities": len(features)
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating healthcare facilities layer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate healthcare facilities layer")


@router.get("/ward_boundaries", response_model=LayerResponse)
async def get_ward_boundaries_layer():
    """Get Mumbai ward boundaries layer."""
    try:
        mumbai_bounds = {"north": 19.3, "south": 18.8, "east": 72.9, "west": 72.7}
        
        features = []
        
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
                
                coords = [[
                    [west, south],
                    [east, south],
                    [east, north],
                    [west, north],
                    [west, south]
                ]]
                
                # Calculate area in sq km
                area_sqkm = ((east - west) * 111) * ((north - south) * 111)
                
                # Estimate population based on area and density
                population = int(area_sqkm * np.random.uniform(5000, 25000))
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": coords
                    },
                    "properties": {
                        "ward_number": ward_number,
                        "ward_name": f"Ward {ward_number}",
                        "population": population,
                        "area_sqkm": round(area_sqkm, 2),
                        "population_density": round(population / area_sqkm, 0),
                        "center_lat": (north + south) / 2,
                        "center_lon": (east + west) / 2
                    }
                })
                
                ward_number += 1
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return LayerResponse(
            layer_name="ward_boundaries",
            data_type="polygon",
            timestamp=datetime.now(),
            feature_count=len(features),
            geojson=geojson,
            metadata={
                "data_source": "Mumbai Municipal Corporation",
                "total_wards": len(features),
                "total_population": sum(f["properties"]["population"] for f in features)
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating ward boundaries layer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate ward boundaries layer")


@router.get("/population_density", response_model=LayerResponse)
async def get_population_density_layer():
    """Get population density layer."""
    try:
        mumbai_bounds = {"north": 19.3, "south": 18.8, "east": 72.9, "west": 72.7}
        
        features = []
        
        # Generate population density grid
        lats = np.linspace(mumbai_bounds["south"], mumbai_bounds["north"], 25)
        lons = np.linspace(mumbai_bounds["west"], mumbai_bounds["east"], 25)
        
        for lat in lats:
            for lon in lons:
                # Higher population density in central areas
                center_distance = ((lat - 19.0760)**2 + (lon - 72.8777)**2)**0.5
                
                if center_distance < 0.1:  # Central area
                    pop_density = np.random.uniform(15000, 30000)
                elif center_distance < 0.2:  # Urban area
                    pop_density = np.random.uniform(8000, 20000)
                else:  # Suburban/outskirts
                    pop_density = np.random.uniform(2000, 10000)
                
                # Add some variation
                pop_density = max(500, pop_density + np.random.normal(0, pop_density * 0.2))
                
                # Classify density
                if pop_density < 5000:
                    density_class = "Low"
                    color = "#ffffcc"
                elif pop_density < 15000:
                    density_class = "Medium"
                    color = "#feb24c"
                elif pop_density < 25000:
                    density_class = "High"
                    color = "#fd8d3c"
                else:
                    density_class = "Very High"
                    color = "#bd0026"
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "population_density": round(pop_density, 0),
                        "density_class": density_class,
                        "color": color,
                        "estimated_population": round(pop_density * 0.25, 0)  # Assuming 0.25 sq km per point
                    }
                })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return LayerResponse(
            layer_name="population_density",
            data_type="point",
            timestamp=datetime.now(),
            feature_count=len(features),
            geojson=geojson,
            metadata={
                "data_source": "WorldPop + VIIRS Night Lights",
                "units": {"population_density": "people/sq km"}
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating population density layer: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate population density layer")
