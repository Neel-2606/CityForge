"""Quick system test to verify Urban Resilience Dashboard backend."""

import asyncio
import sys
from pathlib import Path
import logging

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config import settings
from data_ingestion.nasa_apis import NASADataOrchestrator
from data_ingestion.external_apis import ExternalDataOrchestrator
from preprocessing.data_processor import DataProcessor
from analytics.urban_analytics import UrbanResilienceAnalyzer
from recommendations.recommendation_engine import RecommendationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_data_ingestion():
    """Test data ingestion modules."""
    logger.info("🛰️  Testing NASA data ingestion...")
    
    try:
        nasa_orchestrator = NASADataOrchestrator()
        nasa_datasets = await nasa_orchestrator.ingest_all_data(days_back=3)
        
        assert len(nasa_datasets) > 0, "No NASA datasets ingested"
        logger.info(f"✅ NASA ingestion successful: {list(nasa_datasets.keys())}")
        
        external_orchestrator = ExternalDataOrchestrator()
        external_datasets = await external_orchestrator.ingest_all_external_data()
        
        assert len(external_datasets) > 0, "No external datasets ingested"
        logger.info(f"✅ External ingestion successful: {list(external_datasets.keys())}")
        
        return nasa_datasets, external_datasets
        
    except Exception as e:
        logger.error(f"❌ Data ingestion test failed: {e}")
        raise


async def test_data_processing(nasa_datasets):
    """Test data processing pipeline."""
    logger.info("⚙️  Testing data processing...")
    
    try:
        data_processor = DataProcessor()
        processed_datasets = await data_processor.process_nasa_datasets(nasa_datasets)
        
        assert len(processed_datasets) > 0, "No datasets processed"
        logger.info(f"✅ Data processing successful: {list(processed_datasets.keys())}")
        
        return processed_datasets
        
    except Exception as e:
        logger.error(f"❌ Data processing test failed: {e}")
        raise


async def test_analytics(processed_datasets, external_datasets):
    """Test analytics engine."""
    logger.info("📊 Testing analytics engine...")
    
    try:
        analytics_engine = UrbanResilienceAnalyzer()
        analysis_results = await analytics_engine.run_comprehensive_analysis(
            processed_datasets, external_datasets
        )
        
        assert len(analysis_results) > 0, "No analysis results generated"
        logger.info(f"✅ Analytics successful: {list(analysis_results.keys())}")
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"❌ Analytics test failed: {e}")
        raise


def test_recommendations(analysis_results):
    """Test recommendation engine."""
    logger.info("💡 Testing recommendation engine...")
    
    try:
        recommendation_engine = RecommendationEngine()
        recommendations = recommendation_engine.generate_all_recommendations(analysis_results)
        
        assert len(recommendations) > 0, "No recommendations generated"
        logger.info(f"✅ Recommendations successful: {len(recommendations)} recommendations")
        
        # Test ward summaries
        ward_summaries = recommendation_engine.create_ward_summary(recommendations)
        assert len(ward_summaries) > 0, "No ward summaries generated"
        logger.info(f"✅ Ward summaries successful: {len(ward_summaries)} wards")
        
        # Test city resilience score
        city_score = recommendation_engine.calculate_city_resilience_score(
            analysis_results, recommendations
        )
        assert 'resilience_scores' in city_score, "No resilience scores calculated"
        logger.info(f"✅ City resilience score: {city_score['resilience_scores']['overall_resilience_score']:.1f}/100")
        
        return recommendations, ward_summaries, city_score
        
    except Exception as e:
        logger.error(f"❌ Recommendations test failed: {e}")
        raise


async def test_api_imports():
    """Test API module imports."""
    logger.info("🌐 Testing API imports...")
    
    try:
        from api.routes import health, layers, recommendations
        from main import app
        
        logger.info("✅ API imports successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ API imports test failed: {e}")
        raise


async def run_system_test():
    """Run complete system test."""
    logger.info("🧪 Starting Urban Resilience Dashboard System Test")
    logger.info("=" * 60)
    
    try:
        # Test 1: Data Ingestion
        nasa_datasets, external_datasets = await test_data_ingestion()
        
        # Test 2: Data Processing
        processed_datasets = await test_data_processing(nasa_datasets)
        
        # Test 3: Analytics
        analysis_results = await test_analytics(processed_datasets, external_datasets)
        
        # Test 4: Recommendations
        recommendations, ward_summaries, city_score = test_recommendations(analysis_results)
        
        # Test 5: API Imports
        await test_api_imports()
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("=" * 60)
        logger.info("📊 Test Results Summary:")
        logger.info(f"   • NASA Datasets: {len(nasa_datasets)}")
        logger.info(f"   • External Datasets: {len(external_datasets)}")
        logger.info(f"   • Processed Datasets: {len(processed_datasets)}")
        logger.info(f"   • Analysis Results: {len(analysis_results)}")
        logger.info(f"   • Recommendations: {len(recommendations)}")
        logger.info(f"   • Ward Summaries: {len(ward_summaries)}")
        logger.info(f"   • City Resilience Score: {city_score['resilience_scores']['overall_resilience_score']:.1f}/100")
        logger.info("=" * 60)
        logger.info("🚀 System is ready for deployment!")
        
        return True
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("💥 SYSTEM TEST FAILED!")
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(run_system_test())
    sys.exit(0 if success else 1)
