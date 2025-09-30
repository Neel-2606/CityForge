# 🏙️ Urban Resilience Dashboard - Complete Setup Guide

**NASA International Space Apps Challenge 2025**  
**Complete Step-by-Step Setup Instructions**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Environment Configuration](#environment-configuration)
4. [Python Dependencies](#python-dependencies)
5. [System Testing](#system-testing)
6. [Deployment Options](#deployment-options)
7. [API Testing](#api-testing)
8. [Advanced Configuration](#advanced-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

---

## 🔧 Prerequisites

### Step 1.1: Check Your System

Open **Command Prompt** or **PowerShell** as Administrator and run these commands:

```cmd
# Check Windows version (should be Windows 10/11)
ver

# Check if you have internet connection
ping google.com
```

### Step 1.2: Install Python 3.10+

**Option A: Download from Python.org (Recommended)**

1. Go to https://www.python.org/downloads/
2. Download **Python 3.10** or newer
3. **IMPORTANT**: During installation, check "Add Python to PATH"
4. Click "Install Now"
5. After installation, open new Command Prompt and verify:

```cmd
python --version
# Should show: Python 3.10.x or newer

pip --version
# Should show: pip 23.x.x or newer
```

**Option B: Using Microsoft Store**

1. Open Microsoft Store
2. Search "Python 3.10"
3. Install Python 3.10
4. Verify installation as above

### Step 1.3: Install Git (Optional but Recommended)

1. Go to https://git-scm.com/download/win
2. Download Git for Windows
3. Install with default settings
4. Verify:

```cmd
git --version
# Should show: git version 2.x.x
```

### Step 1.4: Install Docker (Optional - for Production Setup)

1. Go to https://docs.docker.com/desktop/install/windows/
2. Download Docker Desktop for Windows
3. Install and restart your computer
4. Start Docker Desktop
5. Verify:

```cmd
docker --version
# Should show: Docker version 20.x.x

docker-compose --version
# Should show: Docker Compose version 2.x.x
```

### Step 1.5: Install Code Editor (Optional)

**Option A: Visual Studio Code**
1. Go to https://code.visualstudio.com/
2. Download and install
3. Install Python extension

**Option B: Use Notepad++ or any text editor**

---

## 📁 Initial Setup

### Step 2.1: Navigate to Project Directory

Open **Command Prompt** and navigate to your project:

```cmd
# Navigate to your NASA project directory
cd d:\NASA

# Verify you're in the right place
dir
```

You should see these files:
```
main.py
config.py
requirements.txt
Dockerfile
docker-compose.yml
.env.example
start.py
test_system.py
README.md
SETUP_GUIDE.md
```

### Step 2.2: Verify Project Structure

Run this command to see the complete project structure:

```cmd
# Windows command to show directory tree
tree /f
```

Expected structure:
```
d:\NASA\
├── main.py
├── config.py
├── requirements.txt
├── start.py
├── test_system.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── README.md
├── SETUP_GUIDE.md
├── api\
│   ├── __init__.py
│   └── routes\
│       ├── __init__.py
│       ├── health.py
│       ├── layers.py
│       └── recommendations.py
├── analytics\
│   ├── __init__.py
│   └── urban_analytics.py
├── data_ingestion\
│   ├── __init__.py
│   ├── nasa_apis.py
│   └── external_apis.py
├── database\
│   ├── __init__.py
│   ├── connection.py
│   ├── models.py
│   └── init.sql
├── preprocessing\
│   ├── __init__.py
│   └── data_processor.py
├── recommendations\
│   ├── __init__.py
│   └── recommendation_engine.py
└── scripts\
    ├── __init__.py
    ├── data_ingestion_worker.py
    └── run_analysis.py
```

---

## ⚙️ Environment Configuration

### Step 3.1: Create Environment File

```cmd
# Copy the example environment file
copy .env.example .env
```

### Step 3.2: Set Up Supabase Database (Recommended)

**Option A: Supabase Cloud Database (Recommended)**

1. **Create Supabase Account**:
   - Go to https://supabase.com
   - Sign up/Login to your account
   - Click "New Project"

2. **Create Project**:
   - Name: `urban-resilience-mumbai`
   - Database Password: (choose a strong password)
   - Region: Choose closest to your location

3. **Get Credentials**:
   - Go to Project Settings > API
   - Copy these values:
     - Project URL: `https://your-project-id.supabase.co`
     - Anon Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
     - Service Role Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

4. **Create Database Tables**:
   - Go to SQL Editor in Supabase Dashboard
   - Copy and run these SQL queries one by one:

**Enable PostGIS Extension:**
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

**Create Tables:**
```sql
-- Create wards table
CREATE TABLE IF NOT EXISTS wards (
    id SERIAL PRIMARY KEY,
    ward_name VARCHAR(100) NOT NULL,
    ward_number INTEGER,
    geometry GEOMETRY(POLYGON, 4326),
    population INTEGER,
    area_km2 FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create air quality data table
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

-- Create other tables
CREATE TABLE IF NOT EXISTS temperature_data (
    id SERIAL PRIMARY KEY,
    ward_id INTEGER REFERENCES wards(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    temperature_celsius FLOAT,
    heat_index FLOAT,
    geometry GEOMETRY(POINT, 4326)
);

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
```

**Create Indexes:**
```sql
CREATE INDEX IF NOT EXISTS idx_wards_geometry ON wards USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_air_quality_geometry ON air_quality_data USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_air_quality_timestamp ON air_quality_data (timestamp DESC);
```

**Insert Sample Data:**
```sql
INSERT INTO wards (ward_name, ward_number, population, area_km2, geometry) VALUES
('Colaba', 1, 85000, 12.5, ST_GeomFromText('POLYGON((72.81 18.90, 72.84 18.90, 72.84 18.93, 72.81 18.93, 72.81 18.90))', 4326)),
('Fort', 2, 95000, 8.2, ST_GeomFromText('POLYGON((72.82 18.93, 72.85 18.93, 72.85 18.96, 72.82 18.96, 72.82 18.93))', 4326)),
('Worli', 5, 75000, 15.3, ST_GeomFromText('POLYGON((72.81 18.98, 72.84 18.98, 72.84 19.01, 72.81 19.01, 72.81 18.98))', 4326));
```

### Step 3.3: Edit Environment File

Open the `.env` file in your text editor:

```cmd
# Using Notepad
notepad .env

# Or using VS Code (if installed)
code .env
```

### Step 3.4: Configure Environment Variables

Replace the contents of `.env` with these values:

```bash
# =============================================================================
# URBAN RESILIENCE DASHBOARD - ENVIRONMENT CONFIGURATION
# =============================================================================

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/urban_resilience
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=urban_resilience

# NASA API Configuration (For Real Data - Get from https://urs.earthdata.nasa.gov/)
NASA_EARTHDATA_USERNAME=your_actual_nasa_username
NASA_EARTHDATA_PASSWORD=your_actual_nasa_password

# Supabase Database Configuration (Replace with your actual values)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_actual_anon_key
SUPABASE_SERVICE_KEY=your_actual_service_role_key

# External API Configuration (Optional)
WORLDPOP_API_KEY=demo_key
COPERNICUS_API_KEY=demo_key

# Processing Configuration
TARGET_RESOLUTION=500
MAX_WORKERS=4
CACHE_TTL=3600

# Mumbai Geographic Bounds (Don't change unless targeting different city)
MUMBAI_BOUNDS_NORTH=19.3
MUMBAI_BOUNDS_SOUTH=18.8
MUMBAI_BOUNDS_EAST=72.9
MUMBAI_BOUNDS_WEST=72.7
```

**Save the file** (Ctrl+S) and close the editor.

### Step 3.4: Verify Environment File

```cmd
# Check if .env file was created
dir .env

# Show first few lines to verify
type .env | more
```

---

## 🐍 Python Dependencies

### Step 4.1: Upgrade pip (Important)

```cmd
# Upgrade pip to latest version
python -m pip install --upgrade pip
```

### Step 4.2: Install Core Dependencies

```cmd
# Install all required packages (this may take 5-10 minutes)
pip install -r requirements.txt

# Install additional packages for real NASA data
pip install earthaccess==0.8.2 supabase==2.0.2 h5netcdf netcdf4
```

**Expected output:**
```
Collecting fastapi==0.104.1
  Downloading fastapi-0.104.1-py3-none-any.whl
Collecting uvicorn[standard]==0.24.0
  Downloading uvicorn-0.24.0-py3-none-any.whl
...
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 ...
```

### Step 4.3: Verify Installation

```cmd
# Check if key packages are installed
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import geopandas; print('GeoPandas:', geopandas.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
```

### Step 4.4: Handle Installation Issues (If Any)

**If you get Microsoft Visual C++ errors:**

1. Download Microsoft C++ Build Tools:
   - Go to https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Download and install "Build Tools for Visual Studio"
   - Select "C++ build tools" workload

2. Retry installation:
```cmd
pip install -r requirements.txt
```

**If you get GDAL/Fiona errors:**

```cmd
# Install pre-compiled wheels
pip install --find-links https://girder.github.io/large_image_wheels GDAL
pip install --find-links https://girder.github.io/large_image_wheels Fiona
pip install geopandas
```

---

## 🧪 System Testing

### Step 5.1: Run System Test

```cmd
# Run comprehensive system test
python test_system.py
```

**Expected successful output:**
```
🧪 Starting Urban Resilience Dashboard System Test
============================================================
🛰️  Testing NASA data ingestion...
✅ NASA ingestion successful: ['modis_lst', 'aura_omi', 'gpm_precip', 'landsat_ndvi', 'viirs_lights']
🌍 Ingesting external data sources...
✅ External ingestion successful: ['worldpop', 'healthcare', 'green_spaces', 'wards', 'cpcb_pollution']
⚙️  Testing data processing...
✅ Data processing successful: ['modis_lst', 'aura_omi', 'gpm_precip', 'landsat_ndvi', 'viirs_lights']
📊 Testing analytics engine...
✅ Analytics successful: ['air_quality_hotspots', 'ward_air_quality', 'heat_islands', 'flood_zones', 'healthcare_gaps', 'green_space_deficits']
💡 Testing recommendation engine...
✅ Recommendations successful: 20 recommendations
✅ Ward summaries successful: 24 wards
✅ City resilience score: 48.1/100
🌐 Testing API imports...
✅ API imports successful
============================================================
🎉 ALL TESTS PASSED!
============================================================
📊 Test Results Summary:
   • NASA Datasets: 5
   • External Datasets: 5
   • Processed Datasets: 5
   • Analysis Results: 6
   • Recommendations: 20
   • Ward Summaries: 24
   • City Resilience Score: 48.1/100
============================================================
🚀 System is ready for deployment!
```

### Step 5.2: Troubleshoot Test Failures

**If test fails with import errors:**
```cmd
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Ensure you're in the right directory
cd d:\NASA
python test_system.py
```

**If test fails with memory errors:**
```cmd
# Close other applications and retry
python test_system.py
```

---

## 🚀 Deployment Options

### Option A: Quick Start (Recommended for Demo)

### Step 6A.1: Start the Server

```cmd
# Start the Urban Resilience Dashboard backend
python start.py
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════════════╗
║            🏙️  URBAN RESILIENCE DASHBOARD BACKEND 🏙️             ║
║                                                                  ║
║              NASA International Space Apps Challenge 2025        ║
║              Theme: Data Pathways to Healthy Cities              ║
║              Focus City: Mumbai, India                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
🚀 Starting at: 2025-09-30 12:43:02
🌐 API Host: 0.0.0.0:8000
📁 Data Directory: d:\NASA\data
======================================================================
🔧 Initializing Urban Resilience Dashboard...
📁 Created data directories
🎯 System initialization completed successfully
🚀 Starting FastAPI server...
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 6A.2: Verify Server is Running

Open a **new Command Prompt** window and test:

```cmd
# Test health endpoint
curl http://localhost:8000/health/
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-30T12:43:02",
  "version": "1.0.0",
  "uptime_seconds": 1696089782.0,
  "memory_usage_mb": 245.6,
  "cpu_usage_percent": 2.3
}
```

### Option B: Docker Deployment (Production-like)

### Step 6B.1: Start Docker Services

```cmd
# Start all services with Docker
docker-compose up -d
```

**Expected output:**
```
Creating network "nasa_urban_resilience_network" with driver "bridge"
Creating volume "nasa_postgres_data" with local driver
Creating volume "nasa_redis_data" with local driver
Creating urban_resilience_db ... done
Creating urban_resilience_cache ... done
Creating urban_resilience_backend ... done
Creating urban_resilience_worker ... done
```

### Step 6B.2: Check Service Status

```cmd
# Check if all services are running
docker-compose ps
```

**Expected output:**
```
Name                          Command               State           Ports
--------------------------------------------------------------------------------
urban_resilience_backend      uvicorn main:app --host 0 ...   Up      0.0.0.0:8000->8000/tcp
urban_resilience_cache        docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp
urban_resilience_db           docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp
urban_resilience_worker       python -m scripts.data_ing ...   Up
```

### Step 6B.3: View Logs

```cmd
# View backend logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f
```

---

## 🌐 API Testing

### Step 7.1: Test Health Endpoints

```cmd
# Basic health check
curl http://localhost:8000/health/

# Detailed system status
curl http://localhost:8000/health/status

# Simple ping
curl http://localhost:8000/health/ping
```

### Step 7.2: Test Map Layer Endpoints

```cmd
# List available layers
curl http://localhost:8000/layers/

# Get air quality layer
curl http://localhost:8000/layers/air_quality

# Get heat risk layer
curl http://localhost:8000/layers/heat_risk

# Get flood risk layer
curl http://localhost:8000/layers/flood_risk

# Get green cover layer
curl http://localhost:8000/layers/green_cover

# Get healthcare facilities
curl http://localhost:8000/layers/healthcare_facilities

# Get population density
curl http://localhost:8000/layers/population_density

# Get ward boundaries
curl http://localhost:8000/layers/ward_boundaries
```

### Step 7.3: Test Recommendation Endpoints

```cmd
# Get all recommendations
curl http://localhost:8000/recommendations/

# Get recommendations for specific ward
curl http://localhost:8000/recommendations/ward/1

# Get city resilience summary
curl http://localhost:8000/recommendations/summary

# Get air quality analytics
curl http://localhost:8000/recommendations/analytics/air_quality

# Get heat island analytics
curl http://localhost:8000/recommendations/analytics/heat_islands

# Get flood risk analytics
curl http://localhost:8000/recommendations/analytics/flood_risk
```

### Step 7.4: Browser Testing

Open your web browser and visit:

1. **API Documentation**: http://localhost:8000/docs
   - Interactive API documentation with test interface
   
2. **Alternative API Docs**: http://localhost:8000/redoc
   - Clean, readable API documentation

3. **Root Endpoint**: http://localhost:8000/
   - Basic API information

4. **Health Check**: http://localhost:8000/health/
   - System health status

### Step 7.5: Interactive API Testing

1. Go to http://localhost:8000/docs
2. Click on any endpoint (e.g., "GET /layers/air_quality")
3. Click "Try it out"
4. Click "Execute"
5. View the response

---

## 📊 Advanced Configuration

### Step 8.1: Run Full Analysis

```cmd
# Run complete urban resilience analysis
python start.py analysis
```

**Expected output:**
```
🔍 Starting full urban resilience analysis for Mumbai
🛰️  Ingesting NASA satellite data...
✅ NASA ingestion successful: modis_lst
✅ NASA ingestion successful: aura_omi
✅ NASA ingestion successful: gpm_precip
✅ NASA ingestion successful: landsat_ndvi
✅ NASA ingestion successful: viirs_lights
🌍 Ingesting external data sources...
✅ External ingestion successful: worldpop
✅ External ingestion successful: healthcare
✅ External ingestion successful: green_spaces
✅ External ingestion successful: wards
✅ External ingestion successful: cpcb_pollution
⚙️  Processing and normalizing datasets...
✅ Data processing successful: modis_lst
✅ Data processing successful: aura_omi
✅ Data processing successful: gpm_precip
✅ Data processing successful: landsat_ndvi
✅ Data processing successful: viirs_lights
📊 Running comprehensive urban analytics...
✅ Analytics successful: air_quality_hotspots
✅ Analytics successful: ward_air_quality
✅ Analytics successful: heat_islands
✅ Analytics successful: cooling_analysis
✅ Analytics successful: flood_zones
✅ Analytics successful: drainage_analysis
✅ Analytics successful: healthcare_gaps
✅ Analytics successful: healthcare_capacity
✅ Analytics successful: green_space_deficits
💡 Generating actionable recommendations...
✅ Recommendations successful: 47 recommendations
📋 Analysis Results Summary:
==================================================
🏙️  Mumbai Overall Resilience Score: 48.1/100
🏆 City Status: Developing Resilience

🌬️  Air Quality Score: 45.2/100
🌡️  Heat Resilience Score: 52.8/100
🌊 Flood Resilience Score: 38.5/100
🏥 Healthcare Access Score: 61.3/100
🌳 Green Space Score: 42.7/100

📝 Total Recommendations: 47
🚨 Critical Priority: 8
⚠️  High Priority: 15
💰 Total Estimated Cost: $12,450,000

🎯 Top 5 Priority Recommendations:
----------------------------------------
1. Healthcare Access - Establish Primary Health Center
   Ward: Ward 5 | Priority: Critical
   Cost: $800,000 | Timeline: 12-18 months
   Impact: Critical | Population: 125,000

2. Flood Defense - Upgrade Drainage System
   Ward: Ward 1 | Priority: Critical
   Cost: $600,000 | Timeline: 8-14 months
   Impact: Critical | Population: 85,000

3. Air Quality Improvement - Install Monitoring
   Ward: Ward 12 | Priority: High
   Cost: $250,000 | Timeline: 6-12 months
   Impact: High | Population: 95,000

4. Green Space Development - Urban Parks
   Ward: Ward 6 | Priority: High
   Cost: $400,000 | Timeline: 9-15 months
   Impact: Medium | Population: 75,000

5. Heat Mitigation - Cool Roofing
   Ward: Heat Island Zone | Priority: High
   Cost: $200,000 | Timeline: 9-15 months
   Impact: High | Population: 50,000

🏘️  Ward-Level Insights:
------------------------------
Ward 5 (Ward 5):
  • 3 recommendations
  • 2 critical, 1 high priority
  • Est. cost: $1,200,000
  • Population affected: 125,000

Ward 1 (Ward 1):
  • 2 recommendations
  • 1 critical, 1 high priority
  • Est. cost: $800,000
  • Population affected: 85,000

✅ Urban resilience analysis completed successfully!
🚀 Ready for dashboard integration and deployment!
```

### Step 8.2: Start Background Worker

```cmd
# Start background data processing worker
python start.py worker
```

### Step 8.3: Database Operations (Docker only)

```cmd
# Initialize database
docker-compose exec postgres psql -U postgres -d urban_resilience -f /docker-entrypoint-initdb.d/init.sql

# Connect to database
docker-compose exec postgres psql -U postgres -d urban_resilience

# View database tables
docker-compose exec postgres psql -U postgres -d urban_resilience -c "\dt"
```

### Step 8.4: Data Management

```cmd
# Create data directories manually (if needed)
mkdir data
mkdir data\raw
mkdir data\processed
mkdir data\cache

# Check data directory structure
tree data /f
```

---

## 🔧 Troubleshooting

### Issue 1: Port Already in Use

**Error:** `OSError: [WinError 10048] Only one usage of each socket address`

**Solution:**
```cmd
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID 1234 /F

# Or change port in .env file
# Edit .env and change API_PORT=8001
```

### Issue 2: Python Import Errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```cmd
# Verify you're in the right directory
cd d:\NASA

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Issue 3: Permission Errors

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
```cmd
# Run Command Prompt as Administrator
# Right-click Command Prompt -> "Run as administrator"

# Or change directory permissions
icacls d:\NASA /grant %USERNAME%:F /T
```

### Issue 4: Docker Issues

**Error:** `docker: command not found`

**Solution:**
```cmd
# Make sure Docker Desktop is running
# Check Docker status
docker version

# If Docker is not installed, use Python directly
python start.py
```

### Issue 5: Memory Issues

**Error:** `MemoryError` or system becomes slow

**Solution:**
```cmd
# Close other applications
# Reduce MAX_WORKERS in .env file
# Edit .env: MAX_WORKERS=2

# Or run with limited analysis
python start.py server
```

### Issue 6: Firewall/Antivirus Issues

**Error:** Connection refused or blocked

**Solution:**
1. Add Python to Windows Firewall exceptions
2. Temporarily disable antivirus
3. Use localhost instead of 0.0.0.0:
   ```
   # In .env file:
   API_HOST=127.0.0.1
   ```

---

## 🌍 Production Deployment

### Step 10.1: Render Deployment

1. **Create GitHub Repository:**
   ```cmd
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/urban-resilience-mumbai.git
   git push -u origin main
   ```

2. **Deploy to Render:**
   ```cmd
   python deploy.py render
   ```

3. **Follow the instructions provided by the script**

### Step 10.2: Heroku Deployment

1. **Install Heroku CLI:**
   - Download from https://devcenter.heroku.com/articles/heroku-cli

2. **Deploy:**
   ```cmd
   python deploy.py heroku
   ```

3. **Follow the instructions provided by the script**

### Step 10.3: AWS Deployment

1. **Create EC2 Instance**
2. **Install Docker on EC2**
3. **Copy project files**
4. **Run Docker Compose**

---

## 🎯 Quick Reference Commands

### Essential Commands
```cmd
# Setup
copy .env.example .env
pip install -r requirements.txt

# Testing
python test_system.py

# Start Server
python start.py

# Run Analysis
python start.py analysis

# Start Worker
python start.py worker

# Docker
docker-compose up -d
docker-compose ps
docker-compose logs -f
docker-compose down
```

### API Endpoints
```
Health:          http://localhost:8000/health/
Documentation:   http://localhost:8000/docs
Air Quality:     http://localhost:8000/layers/air_quality
Recommendations: http://localhost:8000/recommendations/
City Summary:    http://localhost:8000/recommendations/summary
```

### File Locations
```
Configuration:   d:\NASA\.env
Main App:        d:\NASA\main.py
Startup Script:  d:\NASA\start.py
System Test:     d:\NASA\test_system.py
Documentation:   d:\NASA\README.md
This Guide:      d:\NASA\SETUP_GUIDE.md
```

---

## ✅ Success Checklist

- [ ] Python 3.10+ installed and working
- [ ] All dependencies installed successfully
- [ ] `.env` file created and configured
- [ ] System test passes (`python test_system.py`)
- [ ] API server starts without errors (`python start.py`)
- [ ] Health endpoint responds (`curl http://localhost:8000/health/`)
- [ ] API documentation accessible (`http://localhost:8000/docs`)
- [ ] Map layers return data (`http://localhost:8000/layers/air_quality`)
- [ ] Recommendations endpoint works (`http://localhost:8000/recommendations/`)
- [ ] Full analysis completes (`python start.py analysis`)

---

## 🎉 You're Ready!

Once all items in the success checklist are complete, your **Urban Resilience Dashboard Backend** is fully operational and ready for the NASA Space Apps Challenge!

**Next Steps:**
1. Integrate with your frontend dashboard
2. Customize for your specific demo needs
3. Deploy to cloud platform for public access
4. Prepare your presentation and video demo

**Need Help?** 
- Check the troubleshooting section above
- Run `python test_system.py` to diagnose issues
- Review logs for error messages
- Ensure all prerequisites are properly installed

**Good luck with your NASA Space Apps Challenge submission! 🚀**
