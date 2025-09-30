"""Background worker for data ingestion and processing."""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data_ingestion.nasa_apis import NASADataOrchestrator
from data_ingestion.external_apis import ExternalDataOrchestrator
from preprocessing.data_processor import DataProcessor
from analytics.urban_analytics import UrbanResilienceAnalyzer
from recommendations.recommendation_engine import RecommendationEngine
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataIngestionWorker:
    """Background worker for automated data ingestion and processing."""
    
    def __init__(self):
        self.nasa_orchestrator = NASADataOrchestrator()
        self.external_orchestrator = ExternalDataOrchestrator()
        self.data_processor = DataProcessor()
        self.analytics_engine = UrbanResilienceAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.running = False
        
    async def start(self):
        """Start the background worker."""
        logger.info("Starting Urban Resilience Data Ingestion Worker")
        self.running = True
        
        while self.running:
            try:
                await self.run_data_pipeline()
                
                # Wait for next cycle (run every 6 hours)
                await asyncio.sleep(6 * 3600)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in worker cycle: {e}")
                # Wait 30 minutes before retrying on error
                await asyncio.sleep(30 * 60)
    
    async def run_data_pipeline(self):
        """Run the complete data pipeline."""
        logger.info("Starting data pipeline execution")
        
        try:
            # Step 1: Data Ingestion
            logger.info("Step 1: Ingesting NASA data")
            nasa_datasets = await self.nasa_orchestrator.ingest_all_data(days_back=1)
            await self.nasa_orchestrator.save_datasets(nasa_datasets)
            
            logger.info("Step 1: Ingesting external data")
            external_datasets = await self.external_orchestrator.ingest_all_external_data()
            await self.external_orchestrator.save_datasets(external_datasets)
            
            # Step 2: Data Processing
            logger.info("Step 2: Processing and normalizing data")
            processed_datasets = await self.data_processor.process_nasa_datasets(nasa_datasets)
            await self.data_processor.save_processed_data(processed_datasets)
            
            # Step 3: Analytics
            logger.info("Step 3: Running urban resilience analytics")
            analysis_results = await self.analytics_engine.run_comprehensive_analysis(
                processed_datasets, external_datasets
            )
            
            # Step 4: Generate Recommendations
            logger.info("Step 4: Generating recommendations")
            recommendations = self.recommendation_engine.generate_all_recommendations(analysis_results)
            ward_summaries = self.recommendation_engine.create_ward_summary(recommendations)
            city_score = self.recommendation_engine.calculate_city_resilience_score(
                analysis_results, recommendations
            )
            
            # Step 5: Save Results (in production, save to database)
            logger.info("Step 5: Saving results")
            await self.save_results(analysis_results, recommendations, ward_summaries, city_score)
            
            logger.info("Data pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Data pipeline failed: {e}")
            raise
    
    async def save_results(self, analysis_results, recommendations, ward_summaries, city_score):
        """Save pipeline results to storage."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = settings.processed_data_dir / "results" / timestamp
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Save analysis results
            import json
            import pickle
            
            # Convert GeoDataFrames to GeoJSON for storage
            analysis_json = {}
            for key, value in analysis_results.items():
                if hasattr(value, 'to_json'):  # GeoDataFrame
                    analysis_json[key] = value.to_json()
                elif hasattr(value, 'to_dict'):  # DataFrame
                    analysis_json[key] = value.to_dict('records')
                else:
                    analysis_json[key] = str(value)
            
            with open(results_dir / "analysis_results.json", 'w') as f:
                json.dump(analysis_json, f, indent=2, default=str)
            
            # Save recommendations
            recommendations_data = []
            for rec in recommendations:
                rec_dict = {
                    'ward_number': rec.ward_number,
                    'ward_name': rec.ward_name,
                    'intervention_type': rec.intervention_type.value,
                    'priority': rec.priority.value,
                    'title': rec.title,
                    'description': rec.description,
                    'estimated_cost_usd': rec.estimated_cost_usd,
                    'estimated_impact': rec.estimated_impact,
                    'implementation_timeline': rec.implementation_timeline,
                    'affected_population': rec.affected_population,
                    'metrics': rec.metrics,
                    'coordinates': rec.coordinates
                }
                recommendations_data.append(rec_dict)
            
            with open(results_dir / "recommendations.json", 'w') as f:
                json.dump(recommendations_data, f, indent=2, default=str)
            
            # Save ward summaries
            with open(results_dir / "ward_summaries.json", 'w') as f:
                json.dump(ward_summaries, f, indent=2, default=str)
            
            # Save city resilience score
            with open(results_dir / "city_resilience_score.json", 'w') as f:
                json.dump(city_score, f, indent=2, default=str)
            
            logger.info(f"Results saved to {results_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def stop(self):
        """Stop the worker."""
        logger.info("Stopping data ingestion worker")
        self.running = False


async def main():
    """Main entry point for the worker."""
    worker = DataIngestionWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
    finally:
        worker.stop()


if __name__ == "__main__":
    # Check if running in worker mode
    if os.getenv("WORKER_MODE") == "true":
        asyncio.run(main())
    else:
        logger.info("Worker mode not enabled. Set WORKER_MODE=true to run as background worker.")
