# 🏙️ Urban Resilience Dashboard - Backend System

**NASA International Space Apps Challenge 2025**  
**Theme**: "Data Pathways to Healthy Cities and Human Settlements"  
**Focus City**: Mumbai, India

## 🎯 Mission

The Urban Resilience Dashboard backend is a comprehensive geospatial data pipeline and analytics system that ingests NASA Earth Observation data and partner datasets to assess urban resilience in Mumbai. The system identifies pollution hotspots, urban heat islands, flood-prone zones, healthcare gaps, and green space deficits, then generates actionable recommendations for city planners and policymakers.

## 🚀 Key Features

- **Real-time Data Ingestion**: NASA APIs (MODIS, Aura/OMI, GPM, Landsat, VIIRS) + External sources
- **Geospatial Analytics**: Air quality, heat islands, flood risk, healthcare access, green space analysis
- **Smart Recommendations**: AI-powered intervention suggestions with cost estimates and timelines
- **REST API**: Complete FastAPI backend with GeoJSON map layers and analytics endpoints
- **Scalable Architecture**: Docker containerization, PostgreSQL + PostGIS, background workers
- **Hackathon-Ready**: Synthetic data generators for demo purposes, no heavy ML training required

## 📡 Data Sources

### NASA Data & Resources
- **NASA Earthdata Worldview** → Near real-time imagery, aerosols, rainfall, vegetation
- **MODIS LST** → Land Surface Temperature for heat island detection
- **Aura/OMI** → Air quality (NO₂, SO₂, aerosols)
- **GPM** → Global Precipitation Measurement for flood monitoring
- **SMAP** → Soil Moisture Active Passive for flood/drought risk
- **Landsat 8/9** → NDVI & Land Cover for green space detection
- **VIIRS Night Lights** → Population density & urban growth

### Partner + Supplementary Data
- **OpenStreetMap (OSM)** → Healthcare facilities, parks, transport
- **WorldPop** → Fine-grained population data
- **CPCB** → Central Pollution Control Board ground truth data
- **Mumbai Municipal Corporation** → Ward boundaries and demographics

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Data Ingestion  │───▶│  Preprocessing  │
│                 │    │                  │    │                 │
│ • NASA APIs     │    │ • NASA APIs      │    │ • Normalization │
│ • External APIs │    │ • External APIs  │    │ • Clipping      │
│ • Local Data    │    │ • Schedulers     │    │ • Resampling    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │◀───│   REST API       │◀───│   Analytics     │
│                 │    │                  │    │                 │
│ • Map Layers    │    │ • FastAPI        │    │ • Air Quality   │
│ • Dashboards    │    │ • GeoJSON        │    │ • Heat Islands  │
│ • Visualizations│    │ • Recommendations│    │ • Flood Risk    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐    ┌─────────────────┐
                       │    Database      │◀───│ Recommendations │
                       │                  │    │                 │
                       │ • PostgreSQL     │    │ • Rule Engine   │
                       │ • PostGIS        │    │ • Cost Analysis │
                       │ • Geospatial     │    │ • Prioritization│
                       └──────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

- **Language**: Python 3.10
- **Framework**: FastAPI
- **Database**: PostgreSQL + PostGIS
- **Geospatial**: rasterio, geopandas, shapely, pyproj
- **Data Processing**: pandas, numpy, xarray, scikit-learn
- **Remote Data**: Google Earth Engine API, requests, pydap
- **Containerization**: Docker + Docker Compose
- **Deployment**: Ready for Render/Heroku/AWS

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- Git

### 1. Clone Repository
```bash
git clone <repository-url>
cd NASA
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Option 1: NASA Access Token (Preferred)
# NASA_EARTHDATA_TOKEN=your_access_token

# Option 2: NASA Username/Password
# NASA_EARTHDATA_USERNAME=your_username
# NASA_EARTHDATA_PASSWORD=your_password

# Google Earth Engine
# GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT_KEY=path/to/service-account.json
```

### 3. Docker Deployment (Recommended)
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start database (Docker)
docker-compose up -d postgres

# Run backend
python main.py
```

### 5. Test the API
```bash
# Health check
curl http://localhost:8000/health/

# Get air quality layer
curl http://localhost:8000/layers/air_quality

# Get recommendations
curl http://localhost:8000/recommendations/
```

## 📊 API Endpoints

### Health & Status
- `GET /health/` - Health check
- `GET /health/status` - System status

### Map Layers
- `GET /layers/` - List available layers
- `GET /layers/air_quality` - Air quality heatmap
- `GET /layers/heat_risk` - Urban heat islands
- `GET /layers/flood_risk` - Flood-prone zones
- `GET /layers/green_cover` - Vegetation coverage
- `GET /layers/healthcare_facilities` - Healthcare facilities
- `GET /layers/population_density` - Population distribution
- `GET /layers/ward_boundaries` - Administrative boundaries

### Recommendations & Analytics
- `GET /recommendations/` - All recommendations
- `GET /recommendations/ward/{ward_number}` - Ward-specific recommendations
- `GET /recommendations/summary` - City resilience summary
- `GET /recommendations/analytics/air_quality` - Air quality analytics
- `GET /recommendations/analytics/heat_islands` - Heat island analytics
- `GET /recommendations/analytics/flood_risk` - Flood risk analytics

## 🔄 Data Pipeline Workflow

### 1. Data Ingestion
```python
# NASA APIs
nasa_orchestrator = NASADataOrchestrator()
nasa_datasets = await nasa_orchestrator.ingest_all_data(days_back=7)

# External APIs
external_orchestrator = ExternalDataOrchestrator()
external_datasets = await external_orchestrator.ingest_all_external_data()
```

### 2. Preprocessing & Normalization
```python
data_processor = DataProcessor()
processed_datasets = await data_processor.process_nasa_datasets(nasa_datasets)
```

### 3. Analytics
```python
analytics_engine = UrbanResilienceAnalyzer()
analysis_results = await analytics_engine.run_comprehensive_analysis(
    processed_datasets, external_datasets
)
```

### 4. Recommendations
```python
recommendation_engine = RecommendationEngine()
recommendations = recommendation_engine.generate_all_recommendations(analysis_results)
```

## 🧪 Running Analysis

### Full Analysis Script
```bash
# Run complete urban resilience analysis
python scripts/run_analysis.py
```

### Background Worker
```bash
# Start background data ingestion worker
WORKER_MODE=true python scripts/data_ingestion_worker.py
```

## 📈 Sample Output

```
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
1. Healthcare Access - Establish Primary Health Center
   Ward: Ward 5 | Priority: Critical
   Cost: $800,000 | Timeline: 12-18 months
   Impact: Critical | Population: 125,000

2. Flood Defense - Upgrade Drainage System
   Ward: Ward 1 | Priority: Critical
   Cost: $600,000 | Timeline: 8-14 months
   Impact: Critical | Population: 85,000
```

## 🗄️ Database Schema

### Core Tables
- `wards` - Administrative boundaries
- `air_quality_data` - AQI measurements
- `land_surface_temperature` - Heat data
- `vegetation_index` - NDVI/green cover
- `flood_risk_data` - Flood assessments
- `healthcare_facilities` - Medical facilities
- `green_spaces` - Parks and gardens
- `ward_recommendations` - Generated recommendations

### Spatial Indexes
- PostGIS GIST indexes on all geometry columns
- Temporal indexes on timestamp columns
- Materialized views for ward statistics

## 🌍 Scalability to Other Cities

The system is designed to be easily scalable to other Indian megacities:

### Delhi
```python
# Update config.py
mumbai_bounds = {
    "north": 28.88, "south": 28.40,
    "east": 77.35, "west": 76.84
}
```

### Bangalore
```python
mumbai_bounds = {
    "north": 13.14, "south": 12.83,
    "east": 77.78, "west": 77.46
}
```

### Chennai
```python
mumbai_bounds = {
    "north": 13.23, "south": 12.83,
    "east": 80.35, "west": 80.12
}
```

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/urban_resilience

# NASA APIs
NASA_EARTHDATA_USERNAME=your_username
NASA_EARTHDATA_PASSWORD=your_password
GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT_KEY=path/to/service-account.json

# Processing
TARGET_RESOLUTION=500  # meters
MAX_WORKERS=4
CACHE_TTL=3600  # seconds
```

### City-Specific Configuration
```python
# Mumbai bounds
mumbai_bounds = {
    "north": 19.3, "south": 18.8,
    "east": 72.9, "west": 72.7
}

# Processing parameters
target_resolution = 500  # meters
green_space_target_per_person = 9.0  # sq meters (WHO recommendation)
healthcare_access_threshold = 1.0  # km
```

## 🚀 Deployment Options

### 1. Render (Recommended for Demo)
```bash
# Deploy to Render
git push origin main
# Configure environment variables in Render dashboard
```

### 2. Heroku
```bash
# Create Heroku app
heroku create urban-resilience-mumbai

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main
```

### 3. AWS EC2
```bash
# Launch EC2 instance
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start

# Clone and deploy
git clone <repo>
cd NASA
docker-compose up -d
```

## 🧪 Testing

### Unit Tests
```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=. tests/
```

### API Testing
```bash
# Test all endpoints
python tests/test_api.py

# Load testing
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📊 Performance Metrics

- **Data Ingestion**: ~2-5 minutes for all NASA sources
- **Processing**: ~1-3 minutes for Mumbai region
- **Analytics**: ~30-60 seconds for comprehensive analysis
- **API Response**: <200ms for map layers, <500ms for analytics
- **Memory Usage**: ~2-4GB during processing
- **Storage**: ~500MB per day of processed data

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 NASA Space Apps Challenge 2025

This backend system supports a comprehensive urban resilience dashboard for the NASA International Space Apps Challenge 2025. The system demonstrates:

- **Innovation**: Novel integration of multiple NASA datasets for urban analytics
- **Impact**: Actionable recommendations for city planners and policymakers
- **Scalability**: Easily adaptable to other megacities worldwide
- **Technical Excellence**: Production-ready architecture with proper documentation

### Demo Resources
- **Live API**: [https://urban-resilience-mumbai.onrender.com](https://urban-resilience-mumbai.onrender.com)
- **API Documentation**: [https://urban-resilience-mumbai.onrender.com/docs](https://urban-resilience-mumbai.onrender.com/docs)
- **Frontend Dashboard**: [Link to frontend repository]
- **Video Demo**: [Link to demo video]
- **Presentation**: [Link to presentation deck]

---

**Built with ❤️ for NASA Space Apps Challenge 2025**  
**Team**: Urban Resilience Innovators  
**City**: Mumbai, India  
**Theme**: Data Pathways to Healthy Cities and Human Settlements
#   C i t y F o r g e  
 