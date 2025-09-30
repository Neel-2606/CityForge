-- Database initialization script for Urban Resilience Dashboard
-- This script sets up the PostGIS database with necessary extensions and initial data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- Create custom types
CREATE TYPE aqi_category AS ENUM ('Good', 'Moderate', 'Poor', 'Very Poor', 'Severe');
CREATE TYPE heat_category AS ENUM ('Low', 'Moderate', 'High', 'Extreme');
CREATE TYPE flood_risk_category AS ENUM ('Low', 'Medium', 'High', 'Critical');
CREATE TYPE priority_level AS ENUM ('Low', 'Medium', 'High', 'Critical');
CREATE TYPE intervention_type AS ENUM ('air_quality', 'heat_mitigation', 'flood_defense', 'healthcare', 'green_space', 'infrastructure');

-- Create spatial reference system for Mumbai (if not exists)
-- Using WGS84 (EPSG:4326) as primary CRS
INSERT INTO spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext) 
VALUES (4326, 'EPSG', 4326, '+proj=longlat +datum=WGS84 +no_defs', 
        'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]')
ON CONFLICT (srid) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_wards_geometry ON wards USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_air_quality_location ON air_quality_data USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_air_quality_timestamp ON air_quality_data (timestamp);
CREATE INDEX IF NOT EXISTS idx_lst_location ON land_surface_temperature USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_lst_timestamp ON land_surface_temperature (timestamp);
CREATE INDEX IF NOT EXISTS idx_vegetation_location ON vegetation_index USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_flood_risk_location ON flood_risk_data USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_healthcare_location ON healthcare_facilities USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_green_spaces_geometry ON green_spaces USING GIST (geometry);

-- Create function to calculate distance between points
CREATE OR REPLACE FUNCTION calculate_distance_km(lat1 FLOAT, lon1 FLOAT, lat2 FLOAT, lon2 FLOAT)
RETURNS FLOAT AS $$
BEGIN
    RETURN ST_Distance(
        ST_GeogFromText('POINT(' || lon1 || ' ' || lat1 || ')'),
        ST_GeogFromText('POINT(' || lon2 || ' ' || lat2 || ')')
    ) / 1000.0; -- Convert to kilometers
END;
$$ LANGUAGE plpgsql;

-- Create function to get ward by coordinates
CREATE OR REPLACE FUNCTION get_ward_by_coordinates(lat FLOAT, lon FLOAT)
RETURNS INTEGER AS $$
DECLARE
    ward_num INTEGER;
BEGIN
    SELECT ward_number INTO ward_num
    FROM wards
    WHERE ST_Contains(geometry, ST_GeomFromText('POINT(' || lon || ' ' || lat || ')', 4326))
    LIMIT 1;
    
    RETURN ward_num;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for ward statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS ward_statistics AS
SELECT 
    w.ward_number,
    w.ward_name,
    w.population,
    w.area_sqkm,
    w.population / w.area_sqkm as population_density,
    COUNT(DISTINCT hf.id) as healthcare_facilities_count,
    COUNT(DISTINCT gs.id) as green_spaces_count,
    COALESCE(SUM(gs.area_sqm), 0) as total_green_area_sqm,
    COALESCE(AVG(aq.aqi_value), 0) as avg_aqi,
    COALESCE(AVG(lst.temperature_celsius), 0) as avg_temperature,
    COALESCE(AVG(fr.flood_risk_score), 0) as avg_flood_risk
FROM wards w
LEFT JOIN healthcare_facilities hf ON ST_Within(hf.location, w.geometry)
LEFT JOIN green_spaces gs ON ST_Within(gs.geometry, w.geometry)
LEFT JOIN air_quality_data aq ON ST_Within(aq.location, w.geometry) 
    AND aq.timestamp >= NOW() - INTERVAL '7 days'
LEFT JOIN land_surface_temperature lst ON ST_Within(lst.location, w.geometry) 
    AND lst.timestamp >= NOW() - INTERVAL '7 days'
LEFT JOIN flood_risk_data fr ON ST_Within(fr.location, w.geometry) 
    AND fr.timestamp >= NOW() - INTERVAL '7 days'
GROUP BY w.ward_number, w.ward_name, w.population, w.area_sqkm;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_ward_statistics_ward_number ON ward_statistics (ward_number);

-- Create function to refresh ward statistics
CREATE OR REPLACE FUNCTION refresh_ward_statistics()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ward_statistics;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at column to tables that need it (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ward_recommendations' AND column_name = 'updated_at') THEN
        ALTER TABLE ward_recommendations ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'processing_jobs' AND column_name = 'updated_at') THEN
        ALTER TABLE processing_jobs ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
    END IF;
END $$;

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_ward_recommendations_updated_at ON ward_recommendations;
CREATE TRIGGER update_ward_recommendations_updated_at
    BEFORE UPDATE ON ward_recommendations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_processing_jobs_updated_at ON processing_jobs;
CREATE TRIGGER update_processing_jobs_updated_at
    BEFORE UPDATE ON processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample Mumbai ward boundaries (simplified grid)
INSERT INTO wards (ward_number, ward_name, geometry, population, area_sqkm) VALUES
(1, 'Ward 1 - Colaba', ST_GeomFromText('POLYGON((72.8 18.9, 72.85 18.9, 72.85 18.95, 72.8 18.95, 72.8 18.9))', 4326), 85000, 6.2),
(2, 'Ward 2 - Fort', ST_GeomFromText('POLYGON((72.85 18.9, 72.9 18.9, 72.9 18.95, 72.85 18.95, 72.85 18.9))', 4326), 120000, 4.8),
(3, 'Ward 3 - Marine Lines', ST_GeomFromText('POLYGON((72.8 18.95, 72.85 18.95, 72.85 19.0, 72.8 19.0, 72.8 18.95))', 4326), 95000, 5.5),
(4, 'Ward 4 - Churchgate', ST_GeomFromText('POLYGON((72.85 18.95, 72.9 18.95, 72.9 19.0, 72.85 19.0, 72.85 18.95))', 4326), 110000, 4.2)
ON CONFLICT (ward_number) DO NOTHING;

-- Create sample healthcare facilities
INSERT INTO healthcare_facilities (ward_id, location, name, facility_type, amenity, capacity_beds) VALUES
((SELECT id FROM wards WHERE ward_number = 1 LIMIT 1), ST_GeomFromText('POINT(72.825 18.925)', 4326), 'Colaba General Hospital', 'hospital', 'hospital', 150),
((SELECT id FROM wards WHERE ward_number = 2 LIMIT 1), ST_GeomFromText('POINT(72.875 18.925)', 4326), 'Fort Medical Center', 'clinic', 'clinic', 25),
((SELECT id FROM wards WHERE ward_number = 3 LIMIT 1), ST_GeomFromText('POINT(72.825 18.975)', 4326), 'Marine Lines Pharmacy', 'pharmacy', 'pharmacy', NULL),
((SELECT id FROM wards WHERE ward_number = 4 LIMIT 1), ST_GeomFromText('POINT(72.875 18.975)', 4326), 'Churchgate Health Clinic', 'clinic', 'clinic', 30)
ON CONFLICT DO NOTHING;

-- Create sample green spaces
INSERT INTO green_spaces (ward_id, geometry, name, leisure_type, area_sqm) VALUES
((SELECT id FROM wards WHERE ward_number = 1 LIMIT 1), ST_GeomFromText('POLYGON((72.82 18.92, 72.83 18.92, 72.83 18.93, 72.82 18.93, 72.82 18.92))', 4326), 'Colaba Park', 'park', 12000),
((SELECT id FROM wards WHERE ward_number = 2 LIMIT 1), ST_GeomFromText('POLYGON((72.87 18.92, 72.88 18.92, 72.88 18.93, 72.87 18.93, 72.87 18.92))', 4326), 'Fort Garden', 'garden', 8500),
((SELECT id FROM wards WHERE ward_number = 3 LIMIT 1), ST_GeomFromText('POLYGON((72.82 18.97, 72.83 18.97, 72.83 18.98, 72.82 18.98, 72.82 18.97))', 4326), 'Marine Drive Promenade', 'recreation_ground', 15000)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Create a read-only user for analytics
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'analytics_user') THEN
        CREATE USER analytics_user WITH PASSWORD 'analytics_password';
    END IF;
END $$;

GRANT CONNECT ON DATABASE urban_resilience TO analytics_user;
GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;
GRANT SELECT ON ward_statistics TO analytics_user;

-- Log successful initialization
INSERT INTO processing_jobs (job_type, status, progress, metadata) 
VALUES ('database_initialization', 'completed', 100, '{"message": "Database initialized successfully", "timestamp": "' || NOW() || '"}');

COMMIT;
