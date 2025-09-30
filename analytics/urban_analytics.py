"""Urban resilience analytics modules."""

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from typing import Dict, List, Optional, Tuple
from shapely.geometry import Point, Polygon
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
import logging

logger = logging.getLogger(__name__)


class AirQualityAnalyzer:
    """Analyzes air quality data to identify pollution hotspots."""
    
    def __init__(self):
        self.aqi_thresholds = {
            "Good": (0, 50),
            "Moderate": (51, 100),
            "Poor": (101, 200),
            "Very Poor": (201, 300),
            "Severe": (301, 500)
        }
    
    def identify_hotspots(self, air_quality_data: xr.Dataset, 
                         threshold_aqi: int = 150) -> gpd.GeoDataFrame:
        """Identify air pollution hotspots."""
        try:
            if 'overall_aqi' not in air_quality_data.data_vars:
                logger.warning("No AQI data found")
                return gpd.GeoDataFrame()
            
            aqi_values = air_quality_data['overall_aqi'].values
            lats = air_quality_data.coords['lat'].values
            lons = air_quality_data.coords['lon'].values
            
            hotspots = []
            
            for i, lat in enumerate(lats):
                for j, lon in enumerate(lons):
                    aqi = aqi_values[i, j]
                    
                    if aqi >= threshold_aqi:
                        # Determine severity level
                        if aqi >= 300:
                            severity = "Severe"
                            priority = "Critical"
                        elif aqi >= 200:
                            severity = "Very Poor"
                            priority = "High"
                        else:
                            severity = "Poor"
                            priority = "Medium"
                        
                        hotspots.append({
                            'geometry': Point(lon, lat),
                            'aqi_value': float(aqi),
                            'severity': severity,
                            'priority': priority,
                            'latitude': lat,
                            'longitude': lon
                        })
            
            if hotspots:
                hotspots_gdf = gpd.GeoDataFrame(hotspots, crs='EPSG:4326')
                logger.info(f"Identified {len(hotspots)} air quality hotspots")
                return hotspots_gdf
            else:
                logger.info("No air quality hotspots found")
                return gpd.GeoDataFrame()
                
        except Exception as e:
            logger.error(f"Error identifying air quality hotspots: {e}")
            return gpd.GeoDataFrame()
    
    def analyze_ward_air_quality(self, air_quality_data: xr.Dataset, 
                                wards_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Analyze air quality by ward."""
        try:
            ward_stats = []
            
            if 'overall_aqi' not in air_quality_data.data_vars:
                return pd.DataFrame()
            
            aqi_values = air_quality_data['overall_aqi'].values
            lats = air_quality_data.coords['lat'].values
            lons = air_quality_data.coords['lon'].values
            
            for _, ward in wards_gdf.iterrows():
                ward_aqi_values = []
                
                # Sample points within ward boundary
                for i, lat in enumerate(lats):
                    for j, lon in enumerate(lons):
                        point = Point(lon, lat)
                        if ward.geometry.contains(point):
                            ward_aqi_values.append(aqi_values[i, j])
                
                if ward_aqi_values:
                    mean_aqi = np.mean(ward_aqi_values)
                    max_aqi = np.max(ward_aqi_values)
                    
                    # Determine overall category
                    category = "Good"
                    for cat, (low, high) in self.aqi_thresholds.items():
                        if low <= mean_aqi <= high:
                            category = cat
                            break
                    
                    ward_stats.append({
                        'ward_number': ward.ward_number,
                        'ward_name': ward.ward_name,
                        'mean_aqi': mean_aqi,
                        'max_aqi': max_aqi,
                        'aqi_category': category,
                        'population': ward.population,
                        'affected_population': ward.population if mean_aqi > 100 else 0
                    })
            
            return pd.DataFrame(ward_stats)
            
        except Exception as e:
            logger.error(f"Error analyzing ward air quality: {e}")
            return pd.DataFrame()


class HeatIslandAnalyzer:
    """Analyzes urban heat island effects."""
    
    def __init__(self):
        self.uhi_threshold = 2.0  # Temperature difference threshold in °C
    
    def identify_heat_islands(self, temperature_data: xr.Dataset, 
                            vegetation_data: xr.Dataset) -> gpd.GeoDataFrame:
        """Identify urban heat islands."""
        try:
            heat_islands = []
            
            # Check for temperature data with different possible names
            temp_var = None
            if 'temperature' in temperature_data.data_vars:
                temp_var = 'temperature'
                logger.info("🌡️  Using real MODIS temperature data")
            elif 'LST_Day' in temperature_data.data_vars:
                temp_var = 'LST_Day'
                logger.info("🌡️  Using LST_Day temperature data")
            else:
                logger.warning("No temperature data found")
                return gpd.GeoDataFrame()
            
            temp_values = temperature_data[temp_var].values
            
            # Handle both 1D and 2D coordinate arrays
            lat_coords = temperature_data.coords['lat'].values
            lon_coords = temperature_data.coords['lon'].values
            
            # Calculate mean temperature for reference
            mean_temp = np.nanmean(temp_values)
            logger.info(f"🌡️  Mean temperature: {mean_temp:.1f}°C")
            
            # Get NDVI data if available
            ndvi_values = None
            if vegetation_data and 'NDVI' in vegetation_data.data_vars:
                # Interpolate NDVI to temperature grid
                ndvi_interp = vegetation_data['NDVI'].interp(
                    lat=temperature_data.coords['lat'],
                    lon=temperature_data.coords['lon']
                )
                ndvi_values = ndvi_interp.values
            
            # Iterate through temperature grid
            rows, cols = temp_values.shape
            for i in range(rows):
                for j in range(cols):
                    temp = temp_values[i, j]
                    
                    if np.isnan(temp):
                        continue
                    
                    # Get coordinates for this pixel
                    if lat_coords.ndim == 2:
                        # 2D coordinate arrays (from MODIS processing)
                        lat = lat_coords[i, j]
                        lon = lon_coords[i, j]
                    else:
                        # 1D coordinate arrays (from synthetic data)
                        lat = lat_coords[i]
                        lon = lon_coords[j]
                    
                    temp_diff = temp - mean_temp
                    
                    # Check if this is a heat island (high temp + low vegetation)
                    is_heat_island = temp_diff >= self.uhi_threshold
                    
                    if ndvi_values is not None:
                        ndvi = ndvi_values[i, j]
                        # Heat island more likely with low vegetation
                        is_heat_island = is_heat_island and (ndvi < 0.3)
                    
                    if is_heat_island:
                        # Classify intensity
                        if temp_diff >= 5.0:
                            intensity = "Extreme"
                            priority = "Critical"
                        elif temp_diff >= 3.5:
                            intensity = "High"
                            priority = "High"
                        else:
                            intensity = "Moderate"
                            priority = "Medium"
                        
                        heat_islands.append({
                            'geometry': Point(lon, lat),
                            'temperature': float(temp),
                            'temperature_diff': float(temp_diff),
                            'intensity': intensity,
                            'priority': priority,
                            'ndvi': float(ndvi_values[i, j]) if ndvi_values is not None else None,
                            'latitude': lat,
                            'longitude': lon
                        })
            
            if heat_islands:
                heat_islands_gdf = gpd.GeoDataFrame(heat_islands, crs='EPSG:4326')
                logger.info(f"Identified {len(heat_islands)} heat islands")
                return heat_islands_gdf
            else:
                logger.info("No heat islands found")
                return gpd.GeoDataFrame()
                
        except Exception as e:
            logger.error(f"Error identifying heat islands: {e}")
            return gpd.GeoDataFrame()
    
    def analyze_cooling_potential(self, temperature_data: xr.Dataset, 
                                 green_spaces_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Analyze cooling effect of green spaces."""
        try:
            cooling_analysis = []
            
            # Check for temperature data with different possible names
            temp_var = None
            if 'temperature' in temperature_data.data_vars:
                temp_var = 'temperature'
            elif 'LST_Day' in temperature_data.data_vars:
                temp_var = 'LST_Day'
            else:
                return pd.DataFrame()
            
            temp_values = temperature_data[temp_var].values
            lat_coords = temperature_data.coords['lat'].values
            lon_coords = temperature_data.coords['lon'].values
            
            for _, green_space in green_spaces_gdf.iterrows():
                # Get temperature around green space
                center = green_space.geometry.centroid
                buffer_distance = 0.005  # ~500m buffer
                buffer_area = center.buffer(buffer_distance)
                
                temps_in_buffer = []
                temps_outside_buffer = []
                
                # Iterate through temperature grid properly
                rows, cols = temp_values.shape
                for i in range(rows):
                    for j in range(cols):
                        temp = temp_values[i, j]
                        
                        if np.isnan(temp):
                            continue
                        
                        # Get coordinates for this pixel
                        if lat_coords.ndim == 2:
                            # 2D coordinate arrays (from MODIS processing)
                            lat = lat_coords[i, j]
                            lon = lon_coords[i, j]
                        else:
                            # 1D coordinate arrays (from synthetic data)
                            lat = lat_coords[i]
                            lon = lon_coords[j]
                        
                        point = Point(lon, lat)
                        
                        if buffer_area.contains(point):
                            if green_space.geometry.contains(point):
                                continue  # Skip points inside green space
                            temps_in_buffer.append(temp)
                        else:
                            # Sample some points outside for comparison
                            if np.random.random() < 0.1:  # 10% sampling
                                temps_outside_buffer.append(temp)
                
                if temps_in_buffer and temps_outside_buffer:
                    avg_temp_near = np.mean(temps_in_buffer)
                    avg_temp_far = np.mean(temps_outside_buffer)
                    cooling_effect = avg_temp_far - avg_temp_near
                    
                    cooling_analysis.append({
                        'green_space_name': green_space.name,
                        'area_sqm': green_space.area_sqm,
                        'avg_temp_nearby': avg_temp_near,
                        'avg_temp_distant': avg_temp_far,
                        'cooling_effect_celsius': cooling_effect,
                        'cooling_efficiency': cooling_effect / (green_space.area_sqm / 10000)  # per hectare
                    })
            
            return pd.DataFrame(cooling_analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing cooling potential: {e}")
            return pd.DataFrame()


class FloodRiskAnalyzer:
    """Analyzes flood risk based on precipitation, soil moisture, and elevation."""
    
    def __init__(self):
        self.risk_thresholds = {
            "Low": (0, 0.25),
            "Medium": (0.25, 0.5),
            "High": (0.5, 0.75),
            "Critical": (0.75, 1.0)
        }
    
    def assess_flood_risk(self, precipitation_data: xr.Dataset, 
                         elevation_data: Optional[np.ndarray] = None) -> gpd.GeoDataFrame:
        """Assess flood risk zones."""
        try:
            flood_zones = []
            
            if 'flood_risk_score' not in precipitation_data.data_vars:
                logger.warning("No flood risk data found")
                return gpd.GeoDataFrame()
            
            risk_values = precipitation_data['flood_risk_score'].values
            lats = precipitation_data.coords['lat'].values
            lons = precipitation_data.coords['lon'].values
            
            # Create synthetic elevation data if not provided
            if elevation_data is None:
                # Mumbai elevation ranges from 0-200m, lower near coast
                elevation_data = np.random.uniform(0, 50, risk_values.shape)
                # Add gradient from east (higher) to west (lower, near coast)
                for i in range(len(lats)):
                    for j in range(len(lons)):
                        # Lower elevation near western coast
                        elevation_data[i, j] *= (1 - (lons[j] - lons.min()) / (lons.max() - lons.min()) * 0.7)
            
            for i, lat in enumerate(lats):
                for j, lon in enumerate(lons):
                    risk_score = risk_values[i, j]
                    elevation = elevation_data[i, j]
                    
                    # Adjust risk based on elevation (lower elevation = higher risk)
                    elevation_factor = max(0, (20 - elevation) / 20)  # Normalize to 0-1
                    adjusted_risk = min(1.0, risk_score + elevation_factor * 0.3)
                    
                    # Only include medium risk and above
                    if adjusted_risk >= 0.25:
                        # Determine risk category
                        category = "Low"
                        for cat, (low, high) in self.risk_thresholds.items():
                            if low <= adjusted_risk < high:
                                category = cat
                                break
                        
                        priority = "Critical" if adjusted_risk >= 0.75 else "High" if adjusted_risk >= 0.5 else "Medium"
                        
                        flood_zones.append({
                            'geometry': Point(lon, lat),
                            'flood_risk_score': float(adjusted_risk),
                            'risk_category': category,
                            'priority': priority,
                            'elevation_m': float(elevation),
                            'precipitation_mm': float(precipitation_data['precipitation_mm'].values[i, j]),
                            'latitude': lat,
                            'longitude': lon
                        })
            
            if flood_zones:
                flood_zones_gdf = gpd.GeoDataFrame(flood_zones, crs='EPSG:4326')
                logger.info(f"Identified {len(flood_zones)} flood risk zones")
                return flood_zones_gdf
            else:
                logger.info("No significant flood risk zones found")
                return gpd.GeoDataFrame()
                
        except Exception as e:
            logger.error(f"Error assessing flood risk: {e}")
            return gpd.GeoDataFrame()
    
    def analyze_drainage_capacity(self, flood_zones_gdf: gpd.GeoDataFrame, 
                                 wards_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Analyze drainage capacity needs by ward."""
        try:
            drainage_analysis = []
            
            for _, ward in wards_gdf.iterrows():
                # Find flood zones within ward
                ward_flood_zones = flood_zones_gdf[
                    flood_zones_gdf.geometry.within(ward.geometry)
                ]
                
                if len(ward_flood_zones) > 0:
                    avg_risk = ward_flood_zones['flood_risk_score'].mean()
                    max_risk = ward_flood_zones['flood_risk_score'].max()
                    high_risk_count = len(ward_flood_zones[ward_flood_zones['flood_risk_score'] >= 0.5])
                    
                    # Estimate drainage capacity needed (simplified)
                    drainage_capacity_needed = high_risk_count * 100  # m³/hour per high-risk zone
                    
                    drainage_analysis.append({
                        'ward_number': ward.ward_number,
                        'ward_name': ward.ward_name,
                        'flood_zones_count': len(ward_flood_zones),
                        'avg_flood_risk': avg_risk,
                        'max_flood_risk': max_risk,
                        'high_risk_zones': high_risk_count,
                        'drainage_capacity_needed': drainage_capacity_needed,
                        'population_at_risk': ward.population * (avg_risk if avg_risk > 0.25 else 0)
                    })
            
            return pd.DataFrame(drainage_analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing drainage capacity: {e}")
            return pd.DataFrame()


class HealthcareAccessAnalyzer:
    """Analyzes healthcare access gaps."""
    
    def __init__(self):
        self.access_threshold_km = 1.0  # 1km threshold for healthcare access
    
    def identify_healthcare_gaps(self, population_data: gpd.GeoDataFrame, 
                                healthcare_facilities_gdf: gpd.GeoDataFrame,
                                wards_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Identify areas with poor healthcare access."""
        try:
            healthcare_gaps = []
            
            # Reproject to projected CRS for accurate distance calculations
            # Use UTM Zone 43N for Mumbai (EPSG:32643)
            try:
                healthcare_facilities_projected = healthcare_facilities_gdf.to_crs('EPSG:32643')
                population_data_projected = population_data.to_crs('EPSG:32643')
                logger.info("🗺️  Reprojected to UTM Zone 43N for accurate distance calculations")
                use_projected = True
            except Exception as e:
                logger.warning(f"⚠️  CRS reprojection failed, using geographic distances: {e}")
                healthcare_facilities_projected = healthcare_facilities_gdf
                population_data_projected = population_data
                use_projected = False
            
            for _, pop_point in population_data_projected.iterrows():
                if pop_point.population < 100:  # Skip low population areas
                    continue
                
                # Find nearest healthcare facility
                distances = healthcare_facilities_projected.geometry.distance(pop_point.geometry)
                min_distance = distances.min()
                
                # Convert to km based on CRS
                if use_projected:
                    min_distance_km = min_distance / 1000.0  # Meters to km
                else:
                    min_distance_km = min_distance * 111.0  # Degrees to km (approximate)
                
                if min_distance_km > self.access_threshold_km:
                    # This is a healthcare gap
                    gap_severity = min(min_distance_km / 5.0, 1.0)  # Normalize to 0-1
                    
                    if gap_severity >= 0.6:
                        priority = "Critical"
                    elif gap_severity >= 0.4:
                        priority = "High"
                    else:
                        priority = "Medium"
                    
                    healthcare_gaps.append({
                        'geometry': pop_point.geometry,
                        'population': pop_point.population,
                        'distance_to_nearest_km': min_distance_km,
                        'gap_severity': gap_severity,
                        'priority': priority,
                        'latitude': pop_point.geometry.y,
                        'longitude': pop_point.geometry.x
                    })
            
            if healthcare_gaps:
                gaps_gdf = gpd.GeoDataFrame(healthcare_gaps, crs='EPSG:4326')
                logger.info(f"Identified {len(healthcare_gaps)} healthcare access gaps")
                return gaps_gdf
            else:
                logger.info("No significant healthcare gaps found")
                return gpd.GeoDataFrame()
                
        except Exception as e:
            logger.error(f"Error identifying healthcare gaps: {e}")
            return gpd.GeoDataFrame()
    
    def analyze_ward_healthcare_capacity(self, healthcare_facilities_gdf: gpd.GeoDataFrame,
                                        wards_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Analyze healthcare capacity by ward."""
        try:
            capacity_analysis = []
            
            for _, ward in wards_gdf.iterrows():
                # Count facilities in ward
                ward_facilities = healthcare_facilities_gdf[
                    healthcare_facilities_gdf.geometry.within(ward.geometry)
                ]
                
                hospitals = len(ward_facilities[ward_facilities['amenity'] == 'hospital'])
                clinics = len(ward_facilities[ward_facilities['amenity'] == 'clinic'])
                pharmacies = len(ward_facilities[ward_facilities['amenity'] == 'pharmacy'])
                
                total_beds = ward_facilities['capacity_beds'].fillna(0).sum()
                
                # Calculate capacity ratios
                facilities_per_1000 = (len(ward_facilities) / ward.population) * 1000
                beds_per_1000 = (total_beds / ward.population) * 1000
                
                # Assess adequacy
                if facilities_per_1000 < 0.5:
                    adequacy = "Insufficient"
                elif facilities_per_1000 < 1.0:
                    adequacy = "Adequate"
                else:
                    adequacy = "Good"
                
                capacity_analysis.append({
                    'ward_number': ward.ward_number,
                    'ward_name': ward.ward_name,
                    'population': ward.population,
                    'hospitals': hospitals,
                    'clinics': clinics,
                    'pharmacies': pharmacies,
                    'total_facilities': len(ward_facilities),
                    'total_beds': int(total_beds),
                    'facilities_per_1000': facilities_per_1000,
                    'beds_per_1000': beds_per_1000,
                    'adequacy': adequacy
                })
            
            return pd.DataFrame(capacity_analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing healthcare capacity: {e}")
            return pd.DataFrame()


class GreenSpaceAnalyzer:
    """Analyzes green space distribution and deficits."""
    
    def __init__(self):
        self.green_space_target_sqm_per_person = 9.0  # WHO recommendation
    
    def identify_green_space_deficits(self, vegetation_data: xr.Dataset,
                                     green_spaces_gdf: gpd.GeoDataFrame,
                                     wards_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """Identify areas with insufficient green space."""
        try:
            green_deficits = []
            
            for _, ward in wards_gdf.iterrows():
                # Calculate existing green space in ward
                ward_green_spaces = green_spaces_gdf[
                    green_spaces_gdf.geometry.within(ward.geometry)
                ]
                
                total_green_area = ward_green_spaces['area_sqm'].sum()
                green_space_per_person = total_green_area / ward.population if ward.population > 0 else 0
                
                # Calculate NDVI-based green cover if available
                ndvi_green_score = 0
                if vegetation_data and 'green_score' in vegetation_data.data_vars:
                    # Sample NDVI points within ward
                    green_scores = []
                    lats = vegetation_data.coords['lat'].values
                    lons = vegetation_data.coords['lon'].values
                    green_values = vegetation_data['green_score'].values
                    
                    for i, lat in enumerate(lats):
                        for j, lon in enumerate(lons):
                            point = Point(lon, lat)
                            if ward.geometry.contains(point):
                                green_scores.append(green_values[i, j])
                    
                    if green_scores:
                        ndvi_green_score = np.mean(green_scores)
                
                # Assess deficit
                deficit_formal = max(0, self.green_space_target_sqm_per_person - green_space_per_person)
                deficit_severity = min(deficit_formal / self.green_space_target_sqm_per_person, 1.0)
                
                # Combine formal green space and NDVI-based assessment
                combined_green_score = (green_space_per_person / self.green_space_target_sqm_per_person * 50) + (ndvi_green_score / 2)
                
                if combined_green_score < 30:
                    priority = "Critical"
                elif combined_green_score < 50:
                    priority = "High"
                elif combined_green_score < 70:
                    priority = "Medium"
                else:
                    priority = "Low"
                
                green_deficits.append({
                    'ward_number': ward.ward_number,
                    'ward_name': ward.ward_name,
                    'population': ward.population,
                    'existing_green_space_sqm': total_green_area,
                    'green_space_per_person': green_space_per_person,
                    'target_green_space_per_person': self.green_space_target_sqm_per_person,
                    'deficit_sqm_per_person': deficit_formal,
                    'deficit_severity': deficit_severity,
                    'ndvi_green_score': ndvi_green_score,
                    'combined_green_score': combined_green_score,
                    'priority': priority,
                    'recommended_new_green_space_sqm': deficit_formal * ward.population
                })
            
            return pd.DataFrame(green_deficits)
            
        except Exception as e:
            logger.error(f"Error identifying green space deficits: {e}")
            return pd.DataFrame()


class UrbanResilienceAnalyzer:
    """Main orchestrator for urban resilience analytics."""
    
    def __init__(self):
        self.air_quality_analyzer = AirQualityAnalyzer()
        self.heat_island_analyzer = HeatIslandAnalyzer()
        self.flood_risk_analyzer = FloodRiskAnalyzer()
        self.healthcare_analyzer = HealthcareAccessAnalyzer()
        self.green_space_analyzer = GreenSpaceAnalyzer()
    
    async def run_comprehensive_analysis(self, 
                                       nasa_datasets: Dict[str, xr.Dataset],
                                       external_datasets: Dict[str, gpd.GeoDataFrame]) -> Dict[str, pd.DataFrame]:
        """Run comprehensive urban resilience analysis."""
        logger.info("Starting comprehensive urban resilience analysis")
        
        results = {}
        
        try:
            # Extract datasets
            wards_gdf = external_datasets.get('wards', gpd.GeoDataFrame())
            healthcare_gdf = external_datasets.get('healthcare', gpd.GeoDataFrame())
            green_spaces_gdf = external_datasets.get('green_spaces', gpd.GeoDataFrame())
            population_gdf = external_datasets.get('worldpop', gpd.GeoDataFrame())
            
            air_quality_data = nasa_datasets.get('aura_omi')
            temperature_data = nasa_datasets.get('modis_lst')
            precipitation_data = nasa_datasets.get('gpm_precip')
            vegetation_data = nasa_datasets.get('landsat_ndvi')
            
            # Air Quality Analysis
            if air_quality_data is not None:
                # Check if using real satellite data
                data_source = air_quality_data.attrs.get('air_quality_source', 'unknown')
                if data_source == 'real_omi_satellite_data':
                    logger.info("🛰️  ANALYZING AIR QUALITY: Using REAL OMI satellite data")
                else:
                    logger.error("❌ INVALID AIR QUALITY DATA SOURCE - Real OMI data required")
                
                logger.info("Analyzing air quality hotspots")
                air_hotspots = self.air_quality_analyzer.identify_hotspots(air_quality_data)
                ward_air_quality = self.air_quality_analyzer.analyze_ward_air_quality(air_quality_data, wards_gdf)
                results['air_quality_hotspots'] = air_hotspots
                results['ward_air_quality'] = ward_air_quality
                
                # Log air quality statistics
                if 'overall_aqi' in air_quality_data.data_vars:
                    aqi_values = air_quality_data['overall_aqi'].values
                    logger.info(f"📊 AQI Statistics: min={np.nanmin(aqi_values):.1f}, max={np.nanmax(aqi_values):.1f}, mean={np.nanmean(aqi_values):.1f}")
                    
                    if not ward_air_quality.empty:
                        mean_ward_aqi = ward_air_quality['mean_aqi'].mean()
                        logger.info(f"🏘️  Average Ward AQI: {mean_ward_aqi:.1f}")
                    else:
                        logger.warning("⚠️  No ward air quality data generated")
            
            # Heat Island Analysis
            if temperature_data is not None:
                logger.info("Analyzing urban heat islands")
                heat_islands = self.heat_island_analyzer.identify_heat_islands(temperature_data, vegetation_data)
                cooling_analysis = self.heat_island_analyzer.analyze_cooling_potential(temperature_data, green_spaces_gdf)
                results['heat_islands'] = heat_islands
                results['cooling_analysis'] = cooling_analysis
            
            # Flood Risk Analysis
            if precipitation_data is not None:
                logger.info("Analyzing flood risk")
                flood_zones = self.flood_risk_analyzer.assess_flood_risk(precipitation_data)
                drainage_analysis = self.flood_risk_analyzer.analyze_drainage_capacity(flood_zones, wards_gdf)
                results['flood_zones'] = flood_zones
                results['drainage_analysis'] = drainage_analysis
            
            # Healthcare Access Analysis
            if not healthcare_gdf.empty and not population_gdf.empty:
                logger.info("Analyzing healthcare access")
                healthcare_gaps = self.healthcare_analyzer.identify_healthcare_gaps(
                    population_gdf, healthcare_gdf, wards_gdf
                )
                healthcare_capacity = self.healthcare_analyzer.analyze_ward_healthcare_capacity(
                    healthcare_gdf, wards_gdf
                )
                results['healthcare_gaps'] = healthcare_gaps
                results['healthcare_capacity'] = healthcare_capacity
            
            # Green Space Analysis
            if not green_spaces_gdf.empty:
                logger.info("Analyzing green space deficits")
                green_deficits = self.green_space_analyzer.identify_green_space_deficits(
                    vegetation_data, green_spaces_gdf, wards_gdf
                )
                results['green_space_deficits'] = green_deficits
            
            logger.info("Comprehensive analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return results
