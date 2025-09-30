"""Database models for Urban Resilience Dashboard."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

from .connection import Base


class Ward(Base):
    """Mumbai ward boundaries and metadata."""
    __tablename__ = "wards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_number = Column(Integer, unique=True, nullable=False)
    ward_name = Column(String(100), nullable=False)
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    population = Column(Integer)
    area_sqkm = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class AirQualityData(Base):
    """Air quality measurements and indices."""
    __tablename__ = "air_quality_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=True)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    no2_level = Column(Float)  # µg/m³
    so2_level = Column(Float)  # µg/m³
    pm25_level = Column(Float)  # µg/m³
    pm10_level = Column(Float)  # µg/m³
    aqi_value = Column(Integer)
    aqi_category = Column(String(20))  # Good, Moderate, Poor, Severe
    data_source = Column(String(50))  # NASA_OMI, CPCB, etc.
    created_at = Column(DateTime, default=datetime.utcnow)


class LandSurfaceTemperature(Base):
    """Land surface temperature data."""
    __tablename__ = "land_surface_temperature"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=True)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    temperature_celsius = Column(Float)
    heat_stress_category = Column(String(20))  # Low, Moderate, High, Extreme
    data_source = Column(String(50))  # MODIS_LST
    created_at = Column(DateTime, default=datetime.utcnow)


class VegetationIndex(Base):
    """NDVI and vegetation data."""
    __tablename__ = "vegetation_index"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=True)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    ndvi_value = Column(Float)  # -1 to 1
    green_score = Column(Integer)  # 0 to 100
    land_cover_type = Column(String(50))
    data_source = Column(String(50))  # Landsat8, Landsat9
    created_at = Column(DateTime, default=datetime.utcnow)


class FloodRiskData(Base):
    """Flood risk assessment data."""
    __tablename__ = "flood_risk_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=True)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    rainfall_mm = Column(Float)
    soil_moisture = Column(Float)
    elevation_m = Column(Float)
    flood_risk_score = Column(Float)  # 0 to 1
    risk_category = Column(String(20))  # Low, Medium, High, Critical
    data_source = Column(String(50))  # GPM, SMAP
    created_at = Column(DateTime, default=datetime.utcnow)


class HealthcareFacility(Base):
    """Healthcare facilities from OSM."""
    __tablename__ = "healthcare_facilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=True)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    name = Column(String(200))
    facility_type = Column(String(50))  # hospital, clinic, pharmacy
    amenity = Column(String(50))
    capacity_beds = Column(Integer)
    osm_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class GreenSpace(Base):
    """Parks and green spaces from OSM."""
    __tablename__ = "green_spaces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=True)
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    name = Column(String(200))
    leisure_type = Column(String(50))  # park, garden, playground
    area_sqm = Column(Float)
    osm_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class WardRecommendation(Base):
    """Generated recommendations for each ward."""
    __tablename__ = "ward_recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), nullable=False)
    recommendation_type = Column(String(50))  # healthcare, green_space, flood_defense
    priority = Column(String(20))  # High, Medium, Low
    title = Column(String(200))
    description = Column(Text)
    estimated_cost = Column(Float)
    estimated_impact = Column(String(20))  # High, Medium, Low
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessingJob(Base):
    """Track data processing jobs."""
    __tablename__ = "processing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text)
    metadata = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
