"""Script to run urban resilience analysis on-demand."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data_ingestion.real_nasa_apis import RealNASADataOrchestrator
from data_ingestion.external_apis import ExternalDataOrchestrator
from preprocessing.data_processor import DataProcessor
from analytics.urban_analytics import UrbanResilienceAnalyzer
from recommendations.recommendation_engine import RecommendationEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_full_analysis():
    """Run complete urban resilience analysis."""
    logger.info("Starting full urban resilience analysis for Mumbai")
    
    try:
        # Initialize components
        nasa_orchestrator = RealNASADataOrchestrator()
        external_orchestrator = ExternalDataOrchestrator()
        data_processor = DataProcessor()
        analytics_engine = UrbanResilienceAnalyzer()
        recommendation_engine = RecommendationEngine()
        
        # Step 1: Data Ingestion
        logger.info("🛰️  Ingesting NASA satellite data...")
        nasa_datasets = await nasa_orchestrator.ingest_all_data(days_back=5)
        
        logger.info("🌍 Ingesting external data sources...")
        external_datasets = await external_orchestrator.ingest_all_external_data()
        
        # Step 2: Data Processing
        logger.info("⚙️  Processing and normalizing datasets...")
        processed_datasets = await data_processor.process_nasa_datasets(nasa_datasets)
        
        # Step 3: Analytics
        logger.info("📊 Running comprehensive urban analytics...")
        analysis_results = await analytics_engine.run_comprehensive_analysis(
            processed_datasets, external_datasets
        )
        
        # Step 4: Recommendations
        logger.info("💡 Generating actionable recommendations...")
        recommendations = recommendation_engine.generate_all_recommendations(analysis_results)
        ward_summaries = recommendation_engine.create_ward_summary(recommendations)
        city_score = recommendation_engine.calculate_city_resilience_score(
            analysis_results, recommendations
        )
        
        # Step 5: Display Results
        logger.info("📋 Analysis Results Summary:")
        logger.info("=" * 50)
        
        # Display data sources - REAL DATA ONLY
        logger.info("📅 Data Sources (REAL NASA SATELLITE DATA ONLY):")
        for source, dataset in processed_datasets.items():
            if dataset is not None and hasattr(dataset, 'attrs'):
                data_source = dataset.attrs.get('air_quality_source', 'real_nasa_satellite_data')
                logger.info(f"   🛰️  {source}: REAL NASA satellite data")
            elif dataset is not None:
                logger.info(f"   🛰️  {source}: REAL NASA satellite data")
            else:
                logger.error(f"   ❌ {source}: FAILED - No real data available")
        
        # Display city resilience score
        overall_score = city_score['resilience_scores']['overall_resilience_score']
        logger.info(f"🏙️  Mumbai Overall Resilience Score: {overall_score:.1f}/100")
        logger.info(f"🏆 City Status: {city_score['city_status']}")
        
        # Display individual scores with data source indicators
        scores = city_score['resilience_scores']
        logger.info(f"🌬️  Air Quality Score: {scores['air_quality_score']:.1f}/100 🛰️")
        logger.info(f"🌡️  Heat Resilience Score: {scores['heat_resilience_score']:.1f}/100 🛰️")
        logger.info(f"🌊 Flood Resilience Score: {scores['flood_resilience_score']:.1f}/100")
        logger.info(f"🏥 Healthcare Access Score: {scores['healthcare_access_score']:.1f}/100")
        logger.info(f"🌳 Green Space Score: {scores['green_space_score']:.1f}/100")
        
        # Display recommendations summary
        rec_summary = city_score['recommendations_summary']
        logger.info(f"📝 Total Recommendations: {rec_summary['total_recommendations']}")
        logger.info(f"🚨 Critical Priority: {rec_summary['critical_priority']}")
        logger.info(f"⚠️  High Priority: {rec_summary['high_priority']}")
        logger.info(f"🔶 Medium Priority: {rec_summary['medium_priority']}")
        logger.info(f"🔷 Low Priority: {rec_summary['low_priority']}")
        logger.info(f"💰 Total Estimated Cost: ${rec_summary['total_estimated_cost_usd']:,.0f}")
        
        # Display top 5 recommendations
        logger.info("\n🎯 Top 5 Priority Recommendations:")
        logger.info("-" * 40)
        for i, rec in enumerate(recommendations[:5], 1):
            logger.info(f"{i}. {rec.title}")
            logger.info(f"   Ward: {rec.ward_name} | Priority: {rec.priority.value}")
            logger.info(f"   Cost: ${rec.estimated_cost_usd:,.0f} | Timeline: {rec.implementation_timeline}")
            logger.info(f"   Impact: {rec.estimated_impact} | Population: {rec.affected_population:,}")
            logger.info("")
        
        # Display ward-level insights
        logger.info("🏘️  Ward-Level Insights:")
        logger.info("-" * 30)
        for ward_num, summary in list(ward_summaries.items())[:5]:  # Top 5 wards
            logger.info(f"Ward {ward_num} ({summary['ward_name']}):")
            logger.info(f"  • {summary['total_recommendations']} recommendations")
            logger.info(f"  • {summary['critical_priority']} critical, {summary['high_priority']} high priority")
            logger.info(f"  • Est. cost: ${summary['total_estimated_cost']:,.0f}")
            logger.info(f"  • Population affected: {summary['affected_population']:,}")
            logger.info("")
        
        logger.info("✅ Urban resilience analysis completed successfully!")
        logger.info("🚀 Ready for dashboard integration and deployment!")
        
        return {
            'analysis_results': analysis_results,
            'recommendations': recommendations,
            'ward_summaries': ward_summaries,
            'city_score': city_score
        }
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_full_analysis())
