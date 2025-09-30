"""Data preprocessing and normalization pipeline."""

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from typing import Dict, List, Optional, Tuple
from shapely.geometry import Point, Polygon
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from sklearn.preprocessing import MinMaxScaler
from config import settings
import logging

logger = logging.getLogger(__name__)


class GeospatialProcessor:
    """Handles geospatial data processing and normalization."""
    
    def __init__(self):
        self.mumbai_bounds = settings.mumbai_bounds
        self.target_resolution = settings.target_resolution
        
    def clip_to_mumbai(self, dataset: xr.Dataset) -> xr.Dataset:
        """Clip dataset to Mumbai administrative boundary."""
        try:
            if 'lat' in dataset.coords and 'lon' in dataset.coords:
                lat_vals = dataset.coords['lat'].values
                lon_vals = dataset.coords['lon'].values
                if getattr(lat_vals, 'ndim', 1) == 2 or getattr(lon_vals, 'ndim', 1) == 2:
                    # Already 2-D geolocated grid (e.g., MODIS reprojected). Upstream processor clips; pass through.
                    logger.info("Skipping clip_to_mumbai: 2-D lat/lon grid handled upstream")
                    return dataset
            bounds = self.mumbai_bounds
            clipped = dataset.sel(
                lat=slice(bounds["south"], bounds["north"]),
                lon=slice(bounds["west"], bounds["east"])
            )
            return clipped
        except Exception as e:
            logger.error(f"Error clipping dataset: {e}")
            return dataset

    def resample_to_grid(self, dataset: xr.Dataset, resolution_meters: int = None) -> xr.Dataset:
        """Resample dataset to consistent grid resolution (only for 1-D lat/lon)."""
        if resolution_meters is None:
            resolution_meters = self.target_resolution
        try:
            # If coordinates are 2-D, skip 1-D interpolation; keep native grid
            if 'lat' in dataset.coords and 'lon' in dataset.coords:
                lat_vals = dataset.coords['lat'].values
                lon_vals = dataset.coords['lon'].values
                if getattr(lat_vals, 'ndim', 1) == 2 or getattr(lon_vals, 'ndim', 1) == 2:
                    logger.info("Skipping resample_to_grid: 2-D lat/lon grid; keep native resolution")
                    return dataset

            bounds = self.mumbai_bounds
            # Convert resolution from meters to degrees (approximate)
            lat_res = resolution_meters / 111000  # 1 degree ≈ 111km
            lon_res = resolution_meters / (111000 * np.cos(np.radians(19.0)))  # Adjust for latitude

            # Create new coordinate arrays
            new_lats = np.arange(bounds["south"], bounds["north"], lat_res)
            new_lons = np.arange(bounds["west"], bounds["east"], lon_res)

            # Interpolate to new grid (1-D coordinate case)
            resampled = dataset.interp(lat=new_lats, lon=new_lons, method='linear')
            return resampled
        except Exception as e:
            logger.error(f"Error resampling dataset: {e}")
            return dataset
    
    def create_ward_grid(self, wards_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Create a regular grid aligned with ward boundaries."""
        try:
            bounds = self.mumbai_bounds
            resolution_deg = self.target_resolution / 111000
            
            # Create grid
            x_coords = np.arange(bounds["west"], bounds["east"], resolution_deg)
            y_coords = np.arange(bounds["south"], bounds["north"], resolution_deg)
            
            grid_cells = []
            for i, x in enumerate(x_coords[:-1]):
                for j, y in enumerate(y_coords[:-1]):
                    cell = Polygon([
                        (x, y),
                        (x + resolution_deg, y),
                        (x + resolution_deg, y + resolution_deg),
                        (x, y + resolution_deg),
                        (x, y)
                    ])
                    
                    grid_cells.append({
                        'grid_id': f"{i}_{j}",
                        'geometry': cell,
                        'center_lat': y + resolution_deg/2,
                        'center_lon': x + resolution_deg/2
                    })
            
            grid_gdf = gpd.GeoDataFrame(grid_cells, crs='EPSG:4326')
            
            # Assign ward information to grid cells
            grid_with_wards = gpd.sjoin(grid_gdf, wards_gdf, how='left', predicate='within')
            
            return grid_with_wards
            
        except Exception as e:
            logger.error(f"Error creating ward grid: {e}")
            return gpd.GeoDataFrame()


class DataNormalizer:
    """Normalizes various data types to common scales."""
    
    def __init__(self):
        self.scalers = {}
    
    def normalize_ndvi(self, ndvi_values: np.ndarray) -> np.ndarray:
        """Normalize NDVI values (-1 to 1) to green score (0 to 100)."""
        try:
            # Clip to valid NDVI range
            ndvi_clipped = np.clip(ndvi_values, -1, 1)
            
            # Convert to 0-100 scale
            green_score = ((ndvi_clipped + 1) / 2) * 100
            
            return green_score.astype(int)
            
        except Exception as e:
            logger.error(f"Error normalizing NDVI: {e}")
            return ndvi_values
    
    def normalize_temperature(self, temp_celsius: np.ndarray) -> Dict[str, np.ndarray]:
        """Normalize temperature data and classify heat stress."""
        try:
            # Define heat stress categories
            def classify_heat_stress(temp):
                if temp < 30:
                    return "Low"
                elif temp < 35:
                    return "Moderate"
                elif temp < 40:
                    return "High"
                else:
                    return "Extreme"
            
            # Vectorize the classification function
            classify_vectorized = np.vectorize(classify_heat_stress)
            heat_categories = classify_vectorized(temp_celsius)
            
            # Normalize to 0-100 scale
            temp_normalized = np.clip((temp_celsius - 20) / 25 * 100, 0, 100)
            
            return {
                'temperature_normalized': temp_normalized,
                'heat_stress_category': heat_categories,
                'temperature_celsius': temp_celsius
            }
            
        except Exception as e:
            logger.error(f"Error normalizing temperature: {e}")
            return {'temperature_celsius': temp_celsius}
    
    def normalize_air_quality(self, pollutant_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Normalize air quality data to AQI standards."""
        try:
            # AQI breakpoints (simplified Indian standards)
            aqi_breakpoints = {
                'pm25': [(0, 30, 0, 50), (30, 60, 51, 100), (60, 90, 101, 200), (90, 120, 201, 300), (120, 250, 301, 400)],
                'pm10': [(0, 50, 0, 50), (50, 100, 51, 100), (100, 250, 101, 200), (250, 350, 201, 300), (350, 430, 301, 400)],
                'no2': [(0, 40, 0, 50), (40, 80, 51, 100), (80, 180, 101, 200), (180, 280, 201, 300), (280, 400, 301, 400)],
                'so2': [(0, 40, 0, 50), (40, 80, 51, 100), (80, 380, 101, 200), (380, 800, 201, 300), (800, 1600, 301, 400)]
            }
            
            def calculate_aqi(concentration, pollutant):
                if pollutant not in aqi_breakpoints:
                    return 50  # Default moderate
                
                breakpoints = aqi_breakpoints[pollutant]
                for c_low, c_high, aqi_low, aqi_high in breakpoints:
                    if c_low <= concentration <= c_high:
                        aqi = ((aqi_high - aqi_low) / (c_high - c_low)) * (concentration - c_low) + aqi_low
                        return int(aqi)
                return 400  # Maximum AQI
            
            results = {}
            aqi_values = []
            
            for pollutant, values in pollutant_data.items():
                if pollutant in aqi_breakpoints:
                    pollutant_aqi = np.array([calculate_aqi(val, pollutant) for val in values.flatten()])
                    pollutant_aqi = pollutant_aqi.reshape(values.shape)
                    results[f'{pollutant}_aqi'] = pollutant_aqi
                    aqi_values.append(pollutant_aqi)
                
                results[pollutant] = values
            
            # Overall AQI is the maximum of individual pollutant AQIs
            if aqi_values:
                overall_aqi = np.maximum.reduce(aqi_values)
                
                # Classify AQI categories
                def classify_aqi(aqi):
                    if aqi <= 50:
                        return "Good"
                    elif aqi <= 100:
                        return "Moderate"
                    elif aqi <= 200:
                        return "Poor"
                    elif aqi <= 300:
                        return "Very Poor"
                    else:
                        return "Severe"
                
                aqi_categories = np.vectorize(classify_aqi)(overall_aqi)
                
                results['overall_aqi'] = overall_aqi
                results['aqi_category'] = aqi_categories
            
            return results
            
        except Exception as e:
            logger.error(f"Error normalizing air quality: {e}")
            return pollutant_data
    
    def normalize_precipitation(self, precip_data: np.ndarray, soil_moisture: np.ndarray = None) -> Dict[str, np.ndarray]:
        """Normalize precipitation and calculate flood risk."""
        try:
            # Classify precipitation intensity
            def classify_precip(precip):
                if precip < 2.5:
                    return "Light"
                elif precip < 10:
                    return "Moderate"
                elif precip < 35:
                    return "Heavy"
                else:
                    return "Very Heavy"
            
            precip_categories = np.vectorize(classify_precip)(precip_data)
            
            # Calculate flood risk index (0-1 scale)
            flood_risk = np.clip(precip_data / 50, 0, 1)  # Normalize by 50mm threshold
            
            if soil_moisture is not None:
                # Higher soil moisture increases flood risk
                soil_factor = np.clip(soil_moisture / 0.5, 0, 1)  # Normalize soil moisture
                flood_risk = np.minimum(flood_risk + soil_factor * 0.3, 1.0)
            
            # Classify flood risk
            def classify_flood_risk(risk):
                if risk < 0.25:
                    return "Low"
                elif risk < 0.5:
                    return "Medium"
                elif risk < 0.75:
                    return "High"
                else:
                    return "Critical"
            
            flood_categories = np.vectorize(classify_flood_risk)(flood_risk)
            
            return {
                'precipitation_mm': precip_data,
                'precipitation_category': precip_categories,
                'flood_risk_score': flood_risk,
                'flood_risk_category': flood_categories
            }
            
        except Exception as e:
            logger.error(f"Error normalizing precipitation: {e}")
            return {'precipitation_mm': precip_data}


class DataProcessor:
    """Main data processing orchestrator."""
    
    def __init__(self):
        self.geo_processor = GeospatialProcessor()
        self.normalizer = DataNormalizer()
    
    async def process_nasa_datasets(self, datasets: Dict[str, xr.Dataset]) -> Dict[str, xr.Dataset]:
        """Process and normalize NASA datasets."""
        processed_datasets = {}
        
        for source, dataset in datasets.items():
            try:
                logger.info(f"Processing {source} dataset")
                
                # Clip to Mumbai bounds
                clipped = self.geo_processor.clip_to_mumbai(dataset)
                
                # Resample to consistent grid
                resampled = self.geo_processor.resample_to_grid(clipped)
                
                # Apply source-specific processing
                if source == "modis_lst":
                    processed = self._process_temperature_data(resampled)
                elif source == "aura_omi":
                    processed = self._process_air_quality_data(resampled)
                elif source == "gpm_precip":
                    processed = self._process_precipitation_data(resampled)
                elif source == "landsat_ndvi":
                    processed = self._process_vegetation_data(resampled)
                elif source == "viirs_lights":
                    processed = self._process_nightlights_data(resampled)
                else:
                    processed = resampled
                
                processed_datasets[source] = processed
                logger.info(f"Successfully processed {source} dataset")
                
            except Exception as e:
                logger.error(f"Error processing {source} dataset: {e}")
                processed_datasets[source] = dataset
        
        return processed_datasets
    
    def _process_temperature_data(self, dataset: xr.Dataset) -> xr.Dataset:
        """Process MODIS LST data."""
        try:
            # If already has 'temperature' (processed MODIS), leave as-is
            if 'temperature' in dataset.data_vars:
                return dataset
            # Process day and night temperatures
            for temp_var in ['LST_Day', 'LST_Night']:
                if temp_var in dataset.data_vars:
                    temp_data = dataset[temp_var].values
                    normalized = self.normalizer.normalize_temperature(temp_data)
                    
                    # Add normalized variables to dataset
                    dataset[f'{temp_var}_normalized'] = (dataset[temp_var].dims, normalized['temperature_normalized'])
                    dataset[f'{temp_var}_heat_category'] = (dataset[temp_var].dims, normalized['heat_stress_category'])
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error processing temperature data: {e}")
            return dataset
    
    def _process_air_quality_data(self, dataset: xr.Dataset) -> xr.Dataset:
        """Process Aura OMI air quality data."""
        try:
            logger.info(f"🌬️  Processing air quality data with variables: {list(dataset.data_vars.keys())}")
            pollutant_data = {}
            
            # Extract pollutant data from real OMI
            if 'NO2_column' in dataset.data_vars:
                # Convert column density to surface concentration (more realistic conversion)
                no2_values = dataset['NO2_column'].values
                # OMI NO2 column density is in molecules/cm², convert to µg/m³
                # Typical conversion: 1e15 molecules/cm² ≈ 20-40 µg/m³ depending on conditions
                # Use a more conservative conversion to avoid maxing out AQI
                pollutant_data['no2'] = np.clip(no2_values * 1e15 / 50.0, 0, 200)  # Cap at 200 µg/m³
                logger.info(f"✅ Real NO2 data: range {np.nanmin(no2_values):.2e} to {np.nanmax(no2_values):.2e}")
                logger.info(f"📊 Converted NO2 concentration: {np.nanmin(pollutant_data['no2']):.1f} to {np.nanmax(pollutant_data['no2']):.1f} µg/m³")
            
            if 'SO2_column' in dataset.data_vars:
                so2_values = dataset['SO2_column'].values
                pollutant_data['so2'] = so2_values * 1e15 / 3.0
                logger.info(f"✅ Real SO2 data: range {np.nanmin(so2_values):.2e} to {np.nanmax(so2_values):.2e}")
            
            # Use only real satellite data - NO synthetic PM
            # OMI provides NO2 and SO2, which are sufficient for air quality analysis
            if pollutant_data:
                logger.info(f"🛰️  Using ONLY real satellite pollutant data: {list(pollutant_data.keys())}")
            
            # Normalize air quality data to AQI
            if pollutant_data:
                normalized = self.normalizer.normalize_air_quality(pollutant_data)
                logger.info(f"🔄 Normalized pollutants to AQI: {list(normalized.keys())}")
                
                # Get coordinate dimensions from the dataset
                if 'NO2_column' in dataset.data_vars:
                    coord_dims = dataset['NO2_column'].dims
                elif 'SO2_column' in dataset.data_vars:
                    coord_dims = dataset['SO2_column'].dims
                else:
                    coord_dims = ('lat', 'lon')  # Default
                
                # Add normalized variables to dataset
                for var_name, values in normalized.items():
                    if isinstance(values, np.ndarray):
                        dataset[var_name] = (coord_dims, values)
                        logger.info(f"✅ Added {var_name} with shape {values.shape}")
                
                # Ensure we have overall_aqi for analytics
                if 'overall_aqi' in normalized:
                    aqi_values = normalized['overall_aqi']
                    logger.info(f"🎯 Overall AQI: range {np.nanmin(aqi_values):.1f} to {np.nanmax(aqi_values):.1f}, mean {np.nanmean(aqi_values):.1f}")
                    
                    # Add data source flag
                    dataset.attrs['air_quality_source'] = 'real_omi_satellite_data'
                    logger.info("🛰️  AIR QUALITY: Using REAL OMI satellite data for AQI calculations")
                else:
                    logger.warning("⚠️  overall_aqi not found in normalized data")
            else:
                logger.warning("⚠️  No pollutant data found in OMI dataset")
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error processing air quality data: {e}")
            return dataset
    
    def _process_precipitation_data(self, dataset: xr.Dataset) -> xr.Dataset:
        """Process GPM precipitation data."""
        try:
            if 'precipitation' in dataset.data_vars:
                precip_data = dataset['precipitation'].values
                
                # Add synthetic soil moisture for demo
                soil_moisture = np.random.uniform(0.1, 0.6, precip_data.shape)
                
                normalized = self.normalizer.normalize_precipitation(precip_data, soil_moisture)
                
                # Add normalized variables to dataset
                for var_name, values in normalized.items():
                    if isinstance(values, np.ndarray):
                        dataset[var_name] = (dataset['precipitation'].dims, values)
                
                # Add soil moisture
                dataset['soil_moisture'] = (dataset['precipitation'].dims, soil_moisture)
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error processing precipitation data: {e}")
            return dataset
    
    def _process_vegetation_data(self, dataset: xr.Dataset) -> xr.Dataset:
        """Process Landsat NDVI data."""
        try:
            if 'NDVI' in dataset.data_vars:
                ndvi_data = dataset['NDVI'].values
                green_score = self.normalizer.normalize_ndvi(ndvi_data)
                
                # Add green score to dataset
                dataset['green_score'] = (dataset['NDVI'].dims, green_score)
                
                # Classify land cover based on NDVI
                def classify_land_cover(ndvi):
                    if ndvi < -0.1:
                        return "Water"
                    elif ndvi < 0.1:
                        return "Built-up"
                    elif ndvi < 0.3:
                        return "Sparse Vegetation"
                    elif ndvi < 0.6:
                        return "Moderate Vegetation"
                    else:
                        return "Dense Vegetation"
                
                land_cover = np.vectorize(classify_land_cover)(ndvi_data)
                dataset['land_cover_class'] = (dataset['NDVI'].dims, land_cover)
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error processing vegetation data: {e}")
            return dataset
    
    def _process_nightlights_data(self, dataset: xr.Dataset) -> xr.Dataset:
        """Process VIIRS night lights data."""
        try:
            if 'DNB_radiance' in dataset.data_vars:
                lights_data = dataset['DNB_radiance'].values
                
                # Normalize to population density proxy (0-100 scale)
                lights_normalized = np.clip(np.log1p(lights_data) / np.log1p(100) * 100, 0, 100)
                dataset['population_density_proxy'] = (dataset['DNB_radiance'].dims, lights_normalized)
                
                # Classify urban intensity
                def classify_urban_intensity(lights):
                    if lights < 1:
                        return "Rural"
                    elif lights < 10:
                        return "Suburban"
                    elif lights < 50:
                        return "Urban"
                    else:
                        return "Dense Urban"
                
                urban_class = np.vectorize(classify_urban_intensity)(lights_data)
                dataset['urban_intensity'] = (dataset['DNB_radiance'].dims, urban_class)
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error processing night lights data: {e}")
            return dataset
    
    async def save_processed_data(self, datasets: Dict[str, xr.Dataset]) -> None:
        """Save processed datasets."""
        for source, dataset in datasets.items():
            try:
                output_path = settings.processed_data_dir / f"{source}_processed.nc"
                dataset.to_netcdf(output_path)
                logger.info(f"Saved processed {source} data to {output_path}")
            except Exception as e:
                logger.error(f"Failed to save processed {source} data: {e}")
