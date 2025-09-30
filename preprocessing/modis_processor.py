"""MODIS data preprocessing with proper coordinate conversion."""

import numpy as np
import xarray as xr
from typing import Optional, Tuple
import logging
from pyproj import Transformer
import rasterio
from rasterio.transform import from_bounds

logger = logging.getLogger(__name__)

class MODISProcessor:
    """Process MODIS HDF files and convert to geographic coordinates."""
    
    def __init__(self):
        # MODIS sinusoidal projection parameters
        self.modis_srs = "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs"
        self.geographic_srs = "EPSG:4326"
        
        # MODIS tile bounds in sinusoidal projection (meters)
        # Each tile is 1200x1200 pixels at 1km resolution
        self.tile_size = 1111950.5197665  # meters (1200 * 926.625433...)
        
        # Calculate tile bounds based on MODIS grid system
        self.tile_bounds = self._calculate_tile_bounds()
    
    def get_tile_from_filename(self, filename: str) -> str:
        """Extract MODIS tile ID from filename."""
        # Example: MOD11A1.A2023365.h14v04.061.2024004135620.hdf
        parts = filename.split('.')
        for part in parts:
            if part.startswith('h') and 'v' in part:
                return part
        return 'h25v06'  # Default for Mumbai region
    
    def _calculate_tile_bounds(self) -> dict:
        """Calculate bounds for MODIS tiles using the official grid system."""
        # MODIS sinusoidal grid parameters
        tile_size = 1111950.5197665  # meters per tile
        
        # Common tiles that might contain data for South Asia
        tiles = {}
        
        # Calculate bounds for tiles around India/Mumbai region
        for h in range(14, 28):  # Horizontal tiles covering South Asia
            for v in range(0, 12):   # Vertical tiles covering South Asia
                tile_id = f"h{h:02d}v{v:02d}"
                
                # Calculate sinusoidal bounds
                left = (h - 18) * tile_size  # h=18 is central meridian
                right = left + tile_size
                top = (9 - v) * tile_size    # v=9 is equator
                bottom = top - tile_size
                
                tiles[tile_id] = {
                    'left': left,
                    'bottom': bottom, 
                    'right': right,
                    'top': top
                }
        
        return tiles
    
    def create_geographic_coordinates(self, shape: Tuple[int, int], tile_id: str) -> Tuple[np.ndarray, np.ndarray]:
        """Create lat/lon coordinate arrays for MODIS tile."""
        rows, cols = shape
        
        # Get tile bounds (these are approximate - in production you'd use MODIS metadata)
        if tile_id in self.tile_bounds:
            bounds = self.tile_bounds[tile_id]
        else:
            # Default bounds for Mumbai region (tile h25v06)
            bounds = self.tile_bounds['h25v06']
        
        # Create coordinate arrays in sinusoidal projection
        x = np.linspace(bounds['left'], bounds['right'], cols)
        y = np.linspace(bounds['top'], bounds['bottom'], rows)  # Note: top to bottom
        
        # Create meshgrid
        xx, yy = np.meshgrid(x, y)
        
        # Transform to geographic coordinates
        transformer = Transformer.from_crs(self.modis_srs, self.geographic_srs, always_xy=True)
        lon, lat = transformer.transform(xx.flatten(), yy.flatten())
        
        # Reshape back to grid
        lon_grid = lon.reshape(shape)
        lat_grid = lat.reshape(shape)
        
        return lat_grid, lon_grid
    
    def process_modis_lst(self, ds: xr.Dataset, filename: str, qc_tolerance: int = 1) -> xr.Dataset:
        """Process MODIS LST data and add geographic coordinates.

        qc_tolerance: accept QC_Day values up to this threshold (e.g., 1 preferred, 2/3 as relaxed)
        """
        logger.info("🌡️  Processing MODIS LST data with geographic coordinates...")
        
        try:
            # Get LST data
            if 'LST_Day_1km' in ds.variables:
                lst_day = ds['LST_Day_1km']
                lst_night = ds.get('LST_Night_1km', None)
            else:
                raise ValueError("No LST data found in MODIS file")
            
            # Get data shape
            shape = lst_day.shape
            logger.info(f"📐 MODIS data shape: {shape}")
            
            # Extract tile ID from filename
            tile_id = self.get_tile_from_filename(filename)
            logger.info(f"🗺️  Processing MODIS tile: {tile_id}")
            
            # Create geographic coordinates
            lat_grid, lon_grid = self.create_geographic_coordinates(shape, tile_id)
            
            # Apply quality control filtering
            qc_day = ds.get('QC_Day', None)
            qc_night = ds.get('QC_Night', None)
            
            # Convert LST from Kelvin to Celsius and apply quality filtering
            lst_day_celsius = lst_day - 273.15
            lst_night_celsius = (lst_night - 273.15) if lst_night is not None else None
            
            def _qc_decode(ok_qc: xr.DataArray, qc_tol: int) -> xr.DataArray:
                """Decode MOD11A1 QC bitfield and return boolean mask of acceptable pixels.
                Bits (per v6 doc):
                  bits 0-1: Mandatory QA (0=best,1=good,2=fair,3=poor)
                  bits 2-3: Data quality (0=good,1=average,2=poor,3=other)
                  bit 5: LST error (> 0 indicates error)
                Policy:
                  - Accept mandatory QA in {0,1}; if qc_tol>2 also accept 2 (fair)
                  - Accept data quality in {0,1}; if qc_tol>1 also accept 2 (poor)
                  - Require LST error bit == 0 when available
                """
                qa_mand = (ok_qc & 0b11)  # bits 0-1
                qa_data = ((ok_qc >> 2) & 0b11)  # bits 2-3
                lst_err = ((ok_qc >> 5) & 0b1)  # bit 5

                # Mandatory QA acceptance
                if qc_tol > 2:
                    mand_ok = (qa_mand <= 2)
                else:
                    mand_ok = (qa_mand <= 1)

                # Data quality acceptance
                if qc_tol > 1:
                    data_ok = (qa_data <= 2)
                else:
                    data_ok = (qa_data <= 1)

                # LST error must be 0 when present
                err_ok = (lst_err == 0)

                return mand_ok & data_ok & err_ok

            # Apply quality control masks (day)
            if qc_day is not None:
                qc_mask_day = _qc_decode(qc_day.astype('int64'), qc_tolerance)
                range_mask = (lst_day > 200) & (lst_day < 400)
                good_quality_mask = qc_mask_day & range_mask
                lst_day_celsius = lst_day_celsius.where(good_quality_mask, np.nan)
                logger.info(
                    f"🔍 QC applied (QC tol={qc_tolerance}): accepted={int(good_quality_mask.sum().values)} / {lst_day.size}"
                )
            else:
                # Basic temperature range filter if no QC data
                temp_mask = (lst_day > 200) & (lst_day < 400)
                lst_day_celsius = lst_day_celsius.where(temp_mask, np.nan)
                logger.info(f"🔍 Applied temperature filter: {temp_mask.sum().values} valid pixels out of {lst_day.size}")
            
            # Same for night data
            if lst_night_celsius is not None and qc_night is not None:
                qc_mask_night = _qc_decode(qc_night.astype('int64'), qc_tolerance)
                range_mask_n = (lst_night > 200) & (lst_night < 400)
                good_quality_night = qc_mask_night & range_mask_n
                lst_night_celsius = lst_night_celsius.where(good_quality_night, np.nan)
            
            # Create new dataset with geographic coordinates
            processed_ds = xr.Dataset({
                'temperature': (['lat', 'lon'], lst_day_celsius.values),
                'temperature_night': (['lat', 'lon'], 
                                    lst_night_celsius.values if lst_night_celsius is not None else np.full(shape, np.nan)),
                'quality_day': (['lat', 'lon'], qc_day.values if qc_day is not None else np.zeros(shape)),
                'quality_night': (['lat', 'lon'], qc_night.values if qc_night is not None else np.zeros(shape))
            }, coords={
                'lat': (['lat', 'lon'], lat_grid),
                'lon': (['lat', 'lon'], lon_grid)
            })
            
            # Add metadata
            processed_ds.attrs.update({
                'title': 'MODIS Land Surface Temperature',
                'source': filename,
                'tile_id': tile_id,
                'units_temperature': 'degrees_Celsius',
                'processing': 'Converted from MODIS sinusoidal to geographic coordinates',
                'qc_tolerance': qc_tolerance
            })
            
            # Clip to Mumbai region with better bounds checking
            mumbai_bounds = {
                'lat_min': 18.5, 'lat_max': 19.5,  # Expanded bounds
                'lon_min': 72.5, 'lon_max': 73.2   # Expanded bounds
            }
            
            # Create mask for Mumbai region
            lat_mask = (lat_grid >= mumbai_bounds['lat_min']) & (lat_grid <= mumbai_bounds['lat_max'])
            lon_mask = (lon_grid >= mumbai_bounds['lon_min']) & (lon_grid <= mumbai_bounds['lon_max'])
            mumbai_mask = lat_mask & lon_mask
            
            mumbai_pixels = np.sum(mumbai_mask)
            logger.info(f"🗺️  Mumbai region pixels: {mumbai_pixels} out of {lat_grid.size}")
            
            if mumbai_pixels > 0:
                logger.info(f"✅ Found {mumbai_pixels} pixels in Mumbai region")
                
                # Extract Mumbai subset with indices
                mumbai_indices = np.where(mumbai_mask)
                if len(mumbai_indices[0]) > 0:
                    # Create a smaller dataset focused on Mumbai
                    min_row, max_row = mumbai_indices[0].min(), mumbai_indices[0].max()
                    min_col, max_col = mumbai_indices[1].min(), mumbai_indices[1].max()
                    
                    # Add padding but ensure we stay within bounds
                    pad = 20
                    min_row = max(0, min_row - pad)
                    max_row = min(shape[0], max_row + pad + 1)
                    min_col = max(0, min_col - pad)
                    max_col = min(shape[1], max_col + pad + 1)
                    
                    # Subset the data
                    processed_ds = processed_ds.isel(
                        lat=slice(min_row, max_row),
                        lon=slice(min_col, max_col)
                    )
                    
                    logger.info(f"📍 Mumbai subset shape: {processed_ds.temperature.shape}")
                    
                    # Check if we have valid temperature data after clipping
                    temp_data = processed_ds.temperature.values
                    valid_temps = temp_data[~np.isnan(temp_data)]
                    logger.info(f"🌡️  Valid temperature pixels after clipping: {len(valid_temps)}")
                    
            else:
                logger.warning("⚠️  No pixels found in Mumbai region")
                # Check if the tile covers a different region
                lat_range = f"{lat_grid.min():.2f} to {lat_grid.max():.2f}"
                lon_range = f"{lon_grid.min():.2f} to {lon_grid.max():.2f}"
                logger.info(f"🌍 Tile covers: Lat {lat_range}, Lon {lon_range}")
                logger.info("📋 Using full tile data for analysis")
            
            # Log temperature statistics
            temp_data = processed_ds.temperature.values
            valid_temps = temp_data[~np.isnan(temp_data)]
            processed_ds.attrs['valid_pixel_count'] = int(valid_temps.size)
            if len(valid_temps) > 0:
                logger.info(f"🌡️  Temperature range: {valid_temps.min():.1f}°C to {valid_temps.max():.1f}°C")
                logger.info(f"🌡️  Mean temperature: {valid_temps.mean():.1f}°C")
            
            return processed_ds
            
        except Exception as e:
            logger.error(f"❌ Error processing MODIS data: {e}")
            raise
    
    def clip_to_mumbai(self, ds: xr.Dataset) -> xr.Dataset:
        """Clip dataset to Mumbai bounds."""
        mumbai_bounds = {
            'lat_min': 18.8, 'lat_max': 19.3,
            'lon_min': 72.7, 'lon_max': 72.9
        }
        
        # Simple bounding box clip
        try:
            clipped = ds.sel(
                lat=slice(mumbai_bounds['lat_min'], mumbai_bounds['lat_max']),
                lon=slice(mumbai_bounds['lon_min'], mumbai_bounds['lon_max'])
            )
            logger.info(f"✂️  Clipped to Mumbai bounds: {clipped.temperature.shape}")
            return clipped
        except Exception as e:
            logger.warning(f"⚠️  Could not clip to Mumbai bounds: {e}")
            return ds
