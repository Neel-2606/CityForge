"""Recommendations and analytics endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from recommendations.recommendation_engine import (
    RecommendationEngine, 
    Recommendation, 
    InterventionType, 
    Priority
)

logger = logging.getLogger(__name__)

router = APIRouter()


class RecommendationResponse(BaseModel):
    """Response model for individual recommendations."""
    ward_number: int
    ward_name: str
    intervention_type: str
    priority: str
    title: str
    description: str
    estimated_cost_usd: float
    estimated_impact: str
    implementation_timeline: str
    affected_population: int
    metrics: Dict[str, float]
    coordinates: Optional[List[float]] = None


class WardSummaryResponse(BaseModel):
    """Response model for ward-level summary."""
    ward_number: int
    ward_name: str
    total_recommendations: int
    critical_priority: int
    high_priority: int
    medium_priority: int
    low_priority: int
    total_estimated_cost: float
    intervention_types: List[str]
    affected_population: int
    recommendations: List[Dict[str, Any]]


class CityResilienceResponse(BaseModel):
    """Response model for city resilience score."""
    resilience_scores: Dict[str, float]
    recommendations_summary: Dict[str, Any]
    city_status: str


class AnalyticsResponse(BaseModel):
    """Response model for analytics data."""
    analysis_type: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]


@router.get("/", response_model=List[RecommendationResponse])
async def get_all_recommendations(
    priority_filter: Optional[str] = Query(None, description="Filter by priority (Critical, High, Medium, Low)"),
    intervention_type: Optional[str] = Query(None, description="Filter by intervention type"),
    ward_number: Optional[int] = Query(None, description="Filter by ward number"),
    limit: int = Query(50, description="Maximum number of recommendations to return")
):
    """Get all recommendations with optional filtering."""
    try:
        # Generate synthetic recommendations for demo
        recommendations = await _generate_demo_recommendations()
        
        # Apply filters
        filtered_recs = recommendations
        
        if priority_filter:
            filtered_recs = [r for r in filtered_recs if r.priority.value == priority_filter]
        
        if intervention_type:
            filtered_recs = [r for r in filtered_recs if r.intervention_type.value == intervention_type]
        
        if ward_number:
            filtered_recs = [r for r in filtered_recs if r.ward_number == ward_number]
        
        # Limit results
        filtered_recs = filtered_recs[:limit]
        
        # Convert to response format
        response = []
        for rec in filtered_recs:
            response.append(RecommendationResponse(
                ward_number=rec.ward_number,
                ward_name=rec.ward_name,
                intervention_type=rec.intervention_type.value,
                priority=rec.priority.value,
                title=rec.title,
                description=rec.description,
                estimated_cost_usd=rec.estimated_cost_usd,
                estimated_impact=rec.estimated_impact,
                implementation_timeline=rec.implementation_timeline,
                affected_population=rec.affected_population,
                metrics=rec.metrics,
                coordinates=[rec.coordinates[1], rec.coordinates[0]] if rec.coordinates else None
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.get("/ward/{ward_number}", response_model=WardSummaryResponse)
async def get_ward_recommendations(ward_number: int):
    """Get recommendations summary for a specific ward."""
    try:
        # Generate synthetic ward summary for demo
        recommendations = await _generate_demo_recommendations()
        ward_recs = [r for r in recommendations if r.ward_number == ward_number]
        
        if not ward_recs:
            raise HTTPException(status_code=404, detail=f"No recommendations found for ward {ward_number}")
        
        # Calculate summary statistics
        total_cost = sum(r.estimated_cost_usd for r in ward_recs)
        priority_counts = {
            "critical": len([r for r in ward_recs if r.priority == Priority.CRITICAL]),
            "high": len([r for r in ward_recs if r.priority == Priority.HIGH]),
            "medium": len([r for r in ward_recs if r.priority == Priority.MEDIUM]),
            "low": len([r for r in ward_recs if r.priority == Priority.LOW])
        }
        
        intervention_types = list(set(r.intervention_type.value for r in ward_recs))
        max_population = max(r.affected_population for r in ward_recs) if ward_recs else 0
        
        recommendations_list = []
        for rec in ward_recs:
            recommendations_list.append({
                "title": rec.title,
                "description": rec.description,
                "priority": rec.priority.value,
                "cost": rec.estimated_cost_usd,
                "timeline": rec.implementation_timeline,
                "impact": rec.estimated_impact
            })
        
        return WardSummaryResponse(
            ward_number=ward_number,
            ward_name=ward_recs[0].ward_name,
            total_recommendations=len(ward_recs),
            critical_priority=priority_counts["critical"],
            high_priority=priority_counts["high"],
            medium_priority=priority_counts["medium"],
            low_priority=priority_counts["low"],
            total_estimated_cost=total_cost,
            intervention_types=intervention_types,
            affected_population=max_population,
            recommendations=recommendations_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ward recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ward recommendations")


@router.get("/summary", response_model=CityResilienceResponse)
async def get_city_resilience_summary():
    """Get overall city resilience summary and scores."""
    try:
        # Generate synthetic resilience scores for demo
        resilience_scores = {
            "air_quality_score": 45.2,
            "heat_resilience_score": 52.8,
            "flood_resilience_score": 38.5,
            "healthcare_access_score": 61.3,
            "green_space_score": 42.7,
            "overall_resilience_score": 48.1
        }
        
        recommendations = await _generate_demo_recommendations()
        total_cost = sum(r.estimated_cost_usd for r in recommendations)
        critical_count = len([r for r in recommendations if r.priority == Priority.CRITICAL])
        
        recommendations_summary = {
            "total_recommendations": len(recommendations),
            "critical_priority": critical_count,
            "high_priority": len([r for r in recommendations if r.priority == Priority.HIGH]),
            "medium_priority": len([r for r in recommendations if r.priority == Priority.MEDIUM]),
            "low_priority": len([r for r in recommendations if r.priority == Priority.LOW]),
            "total_estimated_cost_usd": total_cost,
            "avg_cost_per_recommendation": total_cost / len(recommendations) if recommendations else 0,
            "intervention_types": list(set(r.intervention_type.value for r in recommendations))
        }
        
        # Determine city status
        overall_score = resilience_scores["overall_resilience_score"]
        if overall_score >= 80:
            city_status = "Highly Resilient"
        elif overall_score >= 65:
            city_status = "Moderately Resilient"
        elif overall_score >= 50:
            city_status = "Developing Resilience"
        elif overall_score >= 35:
            city_status = "Vulnerable"
        else:
            city_status = "Highly Vulnerable"
        
        return CityResilienceResponse(
            resilience_scores=resilience_scores,
            recommendations_summary=recommendations_summary,
            city_status=city_status
        )
        
    except Exception as e:
        logger.error(f"Error getting city resilience summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get city resilience summary")


@router.get("/analytics/air_quality", response_model=AnalyticsResponse)
async def get_air_quality_analytics():
    """Get air quality analytics data."""
    try:
        # Generate synthetic air quality analytics
        ward_data = []
        for ward_num in range(1, 25):  # 24 wards
            aqi = np.random.uniform(60, 180)
            category = "Good" if aqi <= 50 else "Moderate" if aqi <= 100 else "Poor" if aqi <= 150 else "Very Poor"
            
            ward_data.append({
                "ward_number": ward_num,
                "ward_name": f"Ward {ward_num}",
                "mean_aqi": round(aqi, 1),
                "max_aqi": round(aqi * 1.2, 1),
                "aqi_category": category,
                "population": np.random.randint(50000, 200000),
                "affected_population": np.random.randint(20000, 100000) if aqi > 100 else 0,
                "hotspots_count": np.random.randint(0, 8) if aqi > 120 else 0
            })
        
        # Calculate city-wide statistics
        total_population = sum(w["population"] for w in ward_data)
        affected_population = sum(w["affected_population"] for w in ward_data)
        avg_aqi = np.mean([w["mean_aqi"] for w in ward_data])
        
        analytics_data = {
            "ward_analysis": ward_data,
            "city_statistics": {
                "average_aqi": round(avg_aqi, 1),
                "total_population": total_population,
                "affected_population": affected_population,
                "affected_percentage": round((affected_population / total_population) * 100, 1),
                "wards_with_poor_air": len([w for w in ward_data if w["mean_aqi"] > 100]),
                "total_hotspots": sum(w["hotspots_count"] for w in ward_data)
            },
            "trends": {
                "monthly_aqi_trend": [
                    {"month": "Jan", "aqi": 85},
                    {"month": "Feb", "aqi": 92},
                    {"month": "Mar", "aqi": 105},
                    {"month": "Apr", "aqi": 118},
                    {"month": "May", "aqi": 125},
                    {"month": "Jun", "aqi": 95}
                ]
            }
        }
        
        return AnalyticsResponse(
            analysis_type="air_quality",
            timestamp=datetime.now(),
            data=analytics_data,
            metadata={
                "data_sources": ["NASA Aura/OMI", "CPCB"],
                "measurement_units": {"aqi": "index", "population": "count"},
                "analysis_period": "current_month"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting air quality analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get air quality analytics")


@router.get("/analytics/heat_islands", response_model=AnalyticsResponse)
async def get_heat_island_analytics():
    """Get urban heat island analytics data."""
    try:
        # Generate synthetic heat island data
        heat_zones = []
        for i in range(15):  # 15 heat island zones
            intensity = np.random.choice(["Moderate", "High", "Extreme"], p=[0.5, 0.3, 0.2])
            temp_diff = np.random.uniform(1.5, 6.0)
            
            heat_zones.append({
                "zone_id": i + 1,
                "intensity": intensity,
                "temperature_difference": round(temp_diff, 1),
                "area_sqkm": round(np.random.uniform(0.5, 3.0), 2),
                "affected_population": np.random.randint(5000, 25000),
                "latitude": round(np.random.uniform(18.8, 19.3), 4),
                "longitude": round(np.random.uniform(72.7, 72.9), 4)
            })
        
        # Cooling analysis
        cooling_solutions = [
            {"solution": "Urban Parks", "cooling_potential": 3.2, "cost_per_sqkm": 500000},
            {"solution": "Cool Roofs", "cooling_potential": 2.1, "cost_per_sqkm": 200000},
            {"solution": "Tree Planting", "cooling_potential": 1.8, "cost_per_sqkm": 150000},
            {"solution": "Water Features", "cooling_potential": 2.5, "cost_per_sqkm": 300000}
        ]
        
        analytics_data = {
            "heat_island_zones": heat_zones,
            "city_statistics": {
                "total_heat_islands": len(heat_zones),
                "extreme_zones": len([z for z in heat_zones if z["intensity"] == "Extreme"]),
                "total_affected_population": sum(z["affected_population"] for z in heat_zones),
                "average_temperature_increase": round(np.mean([z["temperature_difference"] for z in heat_zones]), 1),
                "total_affected_area": round(sum(z["area_sqkm"] for z in heat_zones), 2)
            },
            "cooling_solutions": cooling_solutions,
            "seasonal_trends": {
                "monthly_heat_index": [
                    {"month": "Jan", "avg_temp": 28.5},
                    {"month": "Feb", "avg_temp": 30.2},
                    {"month": "Mar", "avg_temp": 33.8},
                    {"month": "Apr", "avg_temp": 36.1},
                    {"month": "May", "avg_temp": 38.7},
                    {"month": "Jun", "avg_temp": 35.4}
                ]
            }
        }
        
        return AnalyticsResponse(
            analysis_type="heat_islands",
            timestamp=datetime.now(),
            data=analytics_data,
            metadata={
                "data_sources": ["NASA MODIS LST", "Landsat NDVI"],
                "measurement_units": {"temperature": "°C", "area": "sq km"},
                "analysis_period": "current_season"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting heat island analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get heat island analytics")


@router.get("/analytics/flood_risk", response_model=AnalyticsResponse)
async def get_flood_risk_analytics():
    """Get flood risk analytics data."""
    try:
        # Generate synthetic flood risk data
        flood_zones = []
        for i in range(20):  # 20 flood risk zones
            risk_level = np.random.choice(["Medium", "High", "Critical"], p=[0.4, 0.4, 0.2])
            risk_score = np.random.uniform(0.3, 0.9)
            
            flood_zones.append({
                "zone_id": i + 1,
                "risk_level": risk_level,
                "risk_score": round(risk_score, 2),
                "elevation_m": round(np.random.uniform(0, 25), 1),
                "drainage_capacity": round(np.random.uniform(50, 200), 1),
                "affected_population": np.random.randint(3000, 15000),
                "latitude": round(np.random.uniform(18.8, 19.3), 4),
                "longitude": round(np.random.uniform(72.7, 72.9), 4)
            })
        
        # Drainage infrastructure analysis
        drainage_needs = []
        for ward_num in range(1, 25):
            capacity_needed = np.random.uniform(100, 500)
            current_capacity = capacity_needed * np.random.uniform(0.4, 0.8)
            
            drainage_needs.append({
                "ward_number": ward_num,
                "current_capacity": round(current_capacity, 1),
                "required_capacity": round(capacity_needed, 1),
                "deficit": round(capacity_needed - current_capacity, 1),
                "upgrade_cost": round((capacity_needed - current_capacity) * 2000, 0)
            })
        
        analytics_data = {
            "flood_risk_zones": flood_zones,
            "city_statistics": {
                "total_flood_zones": len(flood_zones),
                "critical_zones": len([z for z in flood_zones if z["risk_level"] == "Critical"]),
                "total_affected_population": sum(z["affected_population"] for z in flood_zones),
                "average_risk_score": round(np.mean([z["risk_score"] for z in flood_zones]), 2),
                "low_elevation_areas": len([z for z in flood_zones if z["elevation_m"] < 10])
            },
            "drainage_analysis": drainage_needs,
            "monsoon_preparedness": {
                "early_warning_systems": 12,
                "evacuation_centers": 8,
                "emergency_response_teams": 15,
                "flood_barriers": 25
            },
            "rainfall_trends": {
                "monthly_precipitation": [
                    {"month": "Jun", "rainfall_mm": 485},
                    {"month": "Jul", "rainfall_mm": 840},
                    {"month": "Aug", "rainfall_mm": 650},
                    {"month": "Sep", "rainfall_mm": 320},
                    {"month": "Oct", "rainfall_mm": 125}
                ]
            }
        }
        
        return AnalyticsResponse(
            analysis_type="flood_risk",
            timestamp=datetime.now(),
            data=analytics_data,
            metadata={
                "data_sources": ["NASA GPM", "SMAP", "Local Drainage Authority"],
                "measurement_units": {"risk_score": "0-1", "elevation": "meters", "capacity": "m³/hour"},
                "analysis_period": "monsoon_season"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting flood risk analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get flood risk analytics")


async def _generate_demo_recommendations() -> List[Recommendation]:
    """Generate demo recommendations for testing."""
    recommendations = []
    
    # Air Quality Recommendations
    for ward_num in [3, 7, 12, 18]:
        recommendations.append(Recommendation(
            ward_number=ward_num,
            ward_name=f"Ward {ward_num}",
            intervention_type=InterventionType.AIR_QUALITY,
            priority=Priority.HIGH if ward_num in [3, 12] else Priority.MEDIUM,
            title=f"Air Quality Improvement - Install Monitoring",
            description="Install air quality monitoring stations and implement pollution control measures",
            estimated_cost_usd=250000,
            estimated_impact="High",
            implementation_timeline="6-12 months",
            affected_population=np.random.randint(50000, 150000),
            metrics={"current_aqi": np.random.uniform(120, 180), "target_aqi_reduction": 30},
            coordinates=(np.random.uniform(72.7, 72.9), np.random.uniform(18.8, 19.3))
        ))
    
    # Healthcare Recommendations
    for ward_num in [5, 9, 15, 21]:
        recommendations.append(Recommendation(
            ward_number=ward_num,
            ward_name=f"Ward {ward_num}",
            intervention_type=InterventionType.HEALTHCARE,
            priority=Priority.CRITICAL if ward_num in [5, 21] else Priority.HIGH,
            title="Healthcare Access - New Primary Health Center",
            description="Establish new primary health center with emergency services",
            estimated_cost_usd=800000,
            estimated_impact="Critical",
            implementation_timeline="12-18 months",
            affected_population=np.random.randint(80000, 200000),
            metrics={"current_facilities_per_1000": 0.3, "target_facilities_per_1000": 1.0},
            coordinates=(np.random.uniform(72.7, 72.9), np.random.uniform(18.8, 19.3))
        ))
    
    # Green Space Recommendations
    for ward_num in [2, 6, 11, 16, 20]:
        recommendations.append(Recommendation(
            ward_number=ward_num,
            ward_name=f"Ward {ward_num}",
            intervention_type=InterventionType.GREEN_SPACE,
            priority=Priority.HIGH,
            title="Green Space Development - Urban Parks",
            description="Develop new urban parks and green corridors",
            estimated_cost_usd=400000,
            estimated_impact="Medium",
            implementation_timeline="9-15 months",
            affected_population=np.random.randint(60000, 120000),
            metrics={"current_green_space_per_person": 2.5, "target_green_space_per_person": 9.0},
            coordinates=(np.random.uniform(72.7, 72.9), np.random.uniform(18.8, 19.3))
        ))
    
    # Flood Defense Recommendations
    for ward_num in [1, 8, 13, 19]:
        recommendations.append(Recommendation(
            ward_number=ward_num,
            ward_name=f"Ward {ward_num}",
            intervention_type=InterventionType.FLOOD_DEFENSE,
            priority=Priority.CRITICAL if ward_num in [1, 13] else Priority.HIGH,
            title="Flood Defense - Drainage Upgrade",
            description="Upgrade storm water drainage system and install flood barriers",
            estimated_cost_usd=600000,
            estimated_impact="Critical",
            implementation_timeline="8-14 months",
            affected_population=np.random.randint(40000, 100000),
            metrics={"flood_risk_score": 0.75, "drainage_capacity_needed": 300},
            coordinates=(np.random.uniform(72.7, 72.9), np.random.uniform(18.8, 19.3))
        ))
    
    return recommendations
