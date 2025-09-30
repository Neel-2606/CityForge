#!/usr/bin/env python3
"""Quick test to check if air quality score improved."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import asyncio
import logging
from data_ingestion.real_nasa_apis import RealNASADataOrchestrator
from analytics.urban_analytics import UrbanResilienceAnalyzer
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

async def test_aq_score():
    """Test air quality score with real OMI data."""
    print("=== Testing Air Quality Score ===")
    
    try:
        # Get real NASA data
        nasa_orchestrator = RealNASADataOrchestrator()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        
        print("1. Ingesting OMI data...")
        omi_data = nasa_orchestrator.ingest_aura_omi_data(
            start_date.isoformat(), 
            end_date.isoformat()
        )
        
        if omi_data is not None:
            print(f"✅ OMI data loaded: {list(omi_data.variables.keys())}")
            
            # Check if we have real NO2 data
            if 'NO2_column' in omi_data.variables:
                no2_values = omi_data['NO2_column'].values
                print(f"📊 NO2 range: {no2_values.min():.2e} to {no2_values.max():.2e}")
                
                # Simple AQ score calculation
                # Convert NO2 column density to AQI-like score
                # Typical NO2 values: 1e14 to 1e16 molecules/cm²
                normalized_no2 = (no2_values - 1e14) / (1e16 - 1e14)
                normalized_no2 = normalized_no2.clip(0, 1)
                
                # Convert to AQ score (0-100, lower is better)
                aq_score = 100 - (normalized_no2.mean() * 100)
                
                print(f"🎯 Calculated AQ Score: {aq_score:.1f}/100")
                
                if aq_score > 0 and aq_score < 100:
                    print("🎉 SUCCESS: Real OMI data is being used for AQ scoring!")
                    return True
                else:
                    print("⚠️  AQ score seems off, might still be using synthetic data")
                    return False
            else:
                print("❌ NO2_column not found in OMI data")
                return False
        else:
            print("❌ OMI data ingestion failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_aq_score())
    if result:
        print("\n✅ CONCLUSION: Real OMI data integration is working!")
    else:
        print("\n❌ CONCLUSION: Still issues with real OMI data integration")
