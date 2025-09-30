"""Recommendation engine for urban resilience interventions."""

import pandas as pd
import geopandas as gpd
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InterventionType(Enum):
    """Types of urban resilience interventions."""
    AIR_QUALITY = "air_quality"
    HEAT_MITIGATION = "heat_mitigation"
    FLOOD_DEFENSE = "flood_defense"
    HEALTHCARE = "healthcare"
    GREEN_SPACE = "green_space"
    INFRASTRUCTURE = "infrastructure"


class Priority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Recommendation:
    """A single recommendation for urban resilience improvement."""
    ward_number: int
    ward_name: str
    intervention_type: InterventionType
    priority: Priority
    title: str
    description: str
    estimated_cost_usd: float
    estimated_impact: str
    implementation_timeline: str
    affected_population: int
    metrics: Dict[str, float]
    coordinates: Optional[Tuple[float, float]] = None


class AirQualityRecommendationGenerator:
    """Generates air quality improvement recommendations."""
    
    def generate_recommendations(self, ward_air_quality: pd.DataFrame, 
                               air_hotspots: gpd.GeoDataFrame) -> List[Recommendation]:
        """Generate air quality recommendations."""
        recommendations = []
        
        try:
            for _, ward in ward_air_quality.iterrows():
                if ward['mean_aqi'] > 100:  # Poor air quality
                    
                    # Determine intervention based on AQI level
                    if ward['mean_aqi'] > 200:
                        priority = Priority.CRITICAL
                        interventions = [
                            "Implement emergency pollution control measures",
                            "Deploy air purification systems in public spaces",
                            "Restrict heavy vehicle traffic during peak hours"
                        ]
                        cost = 500000
                        timeline = "3-6 months"
                    elif ward['mean_aqi'] > 150:
                        priority = Priority.HIGH
                        interventions = [
                            "Install air quality monitoring stations",
                            "Promote electric vehicle adoption",
                            "Implement green belt around industrial areas"
                        ]
                        cost = 300000
                        timeline = "6-12 months"
                    else:
                        priority = Priority.MEDIUM
                        interventions = [
                            "Increase urban tree plantation",
                            "Promote public transportation usage",
                            "Implement dust control measures"
                        ]
                        cost = 150000
                        timeline = "12-18 months"
                    
                    for i, intervention in enumerate(interventions):
                        recommendations.append(Recommendation(
                            ward_number=ward['ward_number'],
                            ward_name=ward['ward_name'],
                            intervention_type=InterventionType.AIR_QUALITY,
                            priority=priority,
                            title=f"Air Quality Improvement - {intervention.split()[0]} {intervention.split()[1]}",
                            description=intervention,
                            estimated_cost_usd=cost / len(interventions),
                            estimated_impact="High" if ward['mean_aqi'] > 150 else "Medium",
                            implementation_timeline=timeline,
                            affected_population=int(ward['affected_population']),
                            metrics={
                                'current_aqi': ward['mean_aqi'],
                                'target_aqi_reduction': min(50, ward['mean_aqi'] - 100),
                                'population_benefited': ward['affected_population']
                            }
                        ))
            
            logger.info(f"Generated {len(recommendations)} air quality recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating air quality recommendations: {e}")
            return []


class HeatMitigationRecommendationGenerator:
    """Generates heat mitigation recommendations."""
    
    def generate_recommendations(self, heat_islands: gpd.GeoDataFrame,
                               cooling_analysis: pd.DataFrame,
                               ward_data: pd.DataFrame) -> List[Recommendation]:
        """Generate heat mitigation recommendations."""
        recommendations = []
        
        try:
            # Group heat islands by ward (simplified approach)
            if not heat_islands.empty:
                # Count heat islands per approximate area
                heat_island_areas = heat_islands.groupby(
                    [heat_islands.geometry.y.round(2), heat_islands.geometry.x.round(2)]
                ).size().reset_index(name='heat_island_count')
                
                for _, area in heat_island_areas.iterrows():
                    if area['heat_island_count'] >= 3:  # Significant heat island cluster
                        
                        priority = Priority.HIGH if area['heat_island_count'] >= 5 else Priority.MEDIUM
                        
                        interventions = [
                            "Install cool roofing systems on public buildings",
                            "Create urban forest corridors",
                            "Implement misting systems in public areas",
                            "Develop pocket parks with shade structures"
                        ]
                        
                        cost = 200000 if priority == Priority.HIGH else 100000
                        timeline = "9-15 months"
                        
                        # Map heat island to actual ward
                        ward_num = (index % 24) + 1  # Distribute across Mumbai's 24 wards
                        ward_name = f"Ward {ward_num}"
                        
                        for intervention in interventions[:2]:  # Top 2 interventions
                            recommendations.append(Recommendation(
                                ward_number=ward_num,
                                ward_name=ward_name,
                                intervention_type=InterventionType.HEAT_MITIGATION,
                                priority=priority,
                                title=f"Heat Island Mitigation - {intervention.split()[0]} {intervention.split()[1]}",
                                description=intervention,
                                estimated_cost_usd=cost / 2,
                                estimated_impact="High" if priority == Priority.HIGH else "Medium",
                                implementation_timeline=timeline,
                                affected_population=5000,  # Estimated
                                metrics={
                                    'heat_islands_count': area['heat_island_count'],
                                    'expected_temp_reduction': 2.5 if priority == Priority.HIGH else 1.5
                                },
                                coordinates=(area.iloc[1], area.iloc[0])  # lon, lat
                            ))
            
            logger.info(f"Generated {len(recommendations)} heat mitigation recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating heat mitigation recommendations: {e}")
            return []


class FloodDefenseRecommendationGenerator:
    """Generates flood defense recommendations."""
    
    def generate_recommendations(self, drainage_analysis: pd.DataFrame,
                               flood_zones: gpd.GeoDataFrame) -> List[Recommendation]:
        """Generate flood defense recommendations."""
        recommendations = []
        
        try:
            for _, ward in drainage_analysis.iterrows():
                if ward['high_risk_zones'] > 0:
                    
                    if ward['max_flood_risk'] >= 0.75:
                        priority = Priority.CRITICAL
                        interventions = [
                            "Construct emergency flood barriers",
                            "Upgrade storm water drainage system",
                            "Install flood early warning systems"
                        ]
                        cost = 800000
                        timeline = "6-12 months"
                    elif ward['max_flood_risk'] >= 0.5:
                        priority = Priority.HIGH
                        interventions = [
                            "Improve drainage infrastructure",
                            "Create retention ponds",
                            "Implement permeable pavement systems"
                        ]
                        cost = 400000
                        timeline = "12-18 months"
                    else:
                        priority = Priority.MEDIUM
                        interventions = [
                            "Regular drainage maintenance",
                            "Community flood preparedness training",
                            "Install water level monitoring"
                        ]
                        cost = 150000
                        timeline = "6-9 months"
                    
                    for intervention in interventions:
                        recommendations.append(Recommendation(
                            ward_number=ward['ward_number'],
                            ward_name=ward['ward_name'],
                            intervention_type=InterventionType.FLOOD_DEFENSE,
                            priority=priority,
                            title=f"Flood Defense - {intervention.split()[0]} {intervention.split()[1]}",
                            description=intervention,
                            estimated_cost_usd=cost / len(interventions),
                            estimated_impact="Critical" if priority == Priority.CRITICAL else "High",
                            implementation_timeline=timeline,
                            affected_population=int(ward['population_at_risk']),
                            metrics={
                                'flood_zones_count': ward['flood_zones_count'],
                                'max_flood_risk': ward['max_flood_risk'],
                                'drainage_capacity_needed': ward['drainage_capacity_needed']
                            }
                        ))
            
            logger.info(f"Generated {len(recommendations)} flood defense recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating flood defense recommendations: {e}")
            return []


class HealthcareRecommendationGenerator:
    """Generates healthcare improvement recommendations."""
    
    def generate_recommendations(self, healthcare_capacity: pd.DataFrame,
                               healthcare_gaps: gpd.GeoDataFrame) -> List[Recommendation]:
        """Generate healthcare recommendations."""
        recommendations = []
        
        try:
            for _, ward in healthcare_capacity.iterrows():
                if ward['adequacy'] == 'Insufficient':
                    
                    if ward['facilities_per_1000'] < 0.2:
                        priority = Priority.CRITICAL
                        interventions = [
                            "Establish new primary health center",
                            "Deploy mobile medical units",
                            "Set up telemedicine facilities"
                        ]
                        cost = 1000000
                        timeline = "12-24 months"
                    else:
                        priority = Priority.HIGH
                        interventions = [
                            "Expand existing clinic capacity",
                            "Add specialized medical services",
                            "Improve ambulance services"
                        ]
                        cost = 500000
                        timeline = "9-15 months"
                    
                    for intervention in interventions:
                        recommendations.append(Recommendation(
                            ward_number=ward['ward_number'],
                            ward_name=ward['ward_name'],
                            intervention_type=InterventionType.HEALTHCARE,
                            priority=priority,
                            title=f"Healthcare Access - {intervention.split()[0]} {intervention.split()[1]}",
                            description=intervention,
                            estimated_cost_usd=cost / len(interventions),
                            estimated_impact="Critical" if priority == Priority.CRITICAL else "High",
                            implementation_timeline=timeline,
                            affected_population=int(ward['population']),
                            metrics={
                                'current_facilities_per_1000': ward['facilities_per_1000'],
                                'target_facilities_per_1000': 1.0,
                                'additional_facilities_needed': max(1, int((1.0 - ward['facilities_per_1000']) * ward['population'] / 1000))
                            }
                        ))
            
            logger.info(f"Generated {len(recommendations)} healthcare recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating healthcare recommendations: {e}")
            return []


class GreenSpaceRecommendationGenerator:
    """Generates green space development recommendations."""
    
    def generate_recommendations(self, green_deficits: pd.DataFrame) -> List[Recommendation]:
        """Generate green space recommendations."""
        recommendations = []
        
        try:
            for _, ward in green_deficits.iterrows():
                if ward['priority'] in ['Critical', 'High']:
                    
                    if ward['priority'] == 'Critical':
                        priority = Priority.CRITICAL
                        interventions = [
                            "Develop new urban parks",
                            "Create rooftop gardens on public buildings",
                            "Establish community gardens"
                        ]
                        cost = 300000
                        timeline = "12-18 months"
                    else:
                        priority = Priority.HIGH
                        interventions = [
                            "Expand existing green spaces",
                            "Plant street trees",
                            "Create green corridors"
                        ]
                        cost = 150000
                        timeline = "9-12 months"
                    
                    for intervention in interventions:
                        recommendations.append(Recommendation(
                            ward_number=ward['ward_number'],
                            ward_name=ward['ward_name'],
                            intervention_type=InterventionType.GREEN_SPACE,
                            priority=priority,
                            title=f"Green Space Development - {intervention.split()[0]} {intervention.split()[1]}",
                            description=intervention,
                            estimated_cost_usd=cost / len(interventions),
                            estimated_impact="High" if priority == Priority.CRITICAL else "Medium",
                            implementation_timeline=timeline,
                            affected_population=int(ward['population']),
                            metrics={
                                'current_green_space_per_person': ward['green_space_per_person'],
                                'target_green_space_per_person': ward['target_green_space_per_person'],
                                'additional_green_space_needed': ward['recommended_new_green_space_sqm']
                            }
                        ))
            
            logger.info(f"Generated {len(recommendations)} green space recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating green space recommendations: {e}")
            return []


class RecommendationEngine:
    """Main recommendation engine orchestrator."""
    
    def __init__(self):
        self.air_quality_generator = AirQualityRecommendationGenerator()
        self.heat_mitigation_generator = HeatMitigationRecommendationGenerator()
        self.flood_defense_generator = FloodDefenseRecommendationGenerator()
        self.healthcare_generator = HealthcareRecommendationGenerator()
        self.green_space_generator = GreenSpaceRecommendationGenerator()
    
    def generate_all_recommendations(self, analysis_results: Dict) -> List[Recommendation]:
        """Generate comprehensive recommendations from analysis results."""
        logger.info("Generating comprehensive recommendations")
        
        all_recommendations = []
        
        try:
            # Air Quality Recommendations
            if 'ward_air_quality' in analysis_results and 'air_quality_hotspots' in analysis_results:
                air_recs = self.air_quality_generator.generate_recommendations(
                    analysis_results['ward_air_quality'],
                    analysis_results['air_quality_hotspots']
                )
                all_recommendations.extend(air_recs)
            
            # Heat Mitigation Recommendations
            if 'heat_islands' in analysis_results:
                heat_recs = self.heat_mitigation_generator.generate_recommendations(
                    analysis_results['heat_islands'],
                    analysis_results.get('cooling_analysis', pd.DataFrame()),
                    pd.DataFrame()  # ward_data placeholder
                )
                all_recommendations.extend(heat_recs)
            
            # Flood Defense Recommendations
            if 'drainage_analysis' in analysis_results and 'flood_zones' in analysis_results:
                flood_recs = self.flood_defense_generator.generate_recommendations(
                    analysis_results['drainage_analysis'],
                    analysis_results['flood_zones']
                )
                all_recommendations.extend(flood_recs)
            
            # Healthcare Recommendations
            if 'healthcare_capacity' in analysis_results and 'healthcare_gaps' in analysis_results:
                health_recs = self.healthcare_generator.generate_recommendations(
                    analysis_results['healthcare_capacity'],
                    analysis_results['healthcare_gaps']
                )
                all_recommendations.extend(health_recs)
            
            # Green Space Recommendations
            if 'green_space_deficits' in analysis_results:
                green_recs = self.green_space_generator.generate_recommendations(
                    analysis_results['green_space_deficits']
                )
                all_recommendations.extend(green_recs)
            
            # Sort by priority and impact
            priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
            all_recommendations.sort(key=lambda x: (priority_order[x.priority], -x.affected_population))
            
            logger.info(f"Generated {len(all_recommendations)} total recommendations")
            return all_recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def create_ward_summary(self, recommendations: List[Recommendation]) -> Dict[int, Dict]:
        """Create ward-level summary of recommendations."""
        ward_summaries = {}
        
        try:
            for rec in recommendations:
                ward_num = rec.ward_number
                
                if ward_num not in ward_summaries:
                    ward_summaries[ward_num] = {
                        'ward_number': ward_num,
                        'ward_name': rec.ward_name,
                        'total_recommendations': 0,
                        'critical_priority': 0,
                        'high_priority': 0,
                        'medium_priority': 0,
                        'low_priority': 0,
                        'total_estimated_cost': 0,
                        'intervention_types': set(),
                        'affected_population': 0,
                        'recommendations': []
                    }
                
                summary = ward_summaries[ward_num]
                summary['total_recommendations'] += 1
                summary['total_estimated_cost'] += rec.estimated_cost_usd
                summary['intervention_types'].add(rec.intervention_type.value)
                summary['affected_population'] = max(summary['affected_population'], rec.affected_population)
                summary['recommendations'].append({
                    'title': rec.title,
                    'description': rec.description,
                    'priority': rec.priority.value,
                    'cost': rec.estimated_cost_usd,
                    'timeline': rec.implementation_timeline,
                    'impact': rec.estimated_impact
                })
                
                # Count by priority
                if rec.priority == Priority.CRITICAL:
                    summary['critical_priority'] += 1
                elif rec.priority == Priority.HIGH:
                    summary['high_priority'] += 1
                elif rec.priority == Priority.MEDIUM:
                    summary['medium_priority'] += 1
                else:
                    summary['low_priority'] += 1
            
            # Convert sets to lists for JSON serialization
            for summary in ward_summaries.values():
                summary['intervention_types'] = list(summary['intervention_types'])
            
            return ward_summaries
            
        except Exception as e:
            logger.error(f"Error creating ward summary: {e}")
            return {}
    
    def calculate_city_resilience_score(self, analysis_results: Dict, 
                                      recommendations: List[Recommendation]) -> Dict:
        """Calculate overall city resilience score."""
        try:
            scores = {
                'air_quality_score': 50,  # Default neutral score
                'heat_resilience_score': 50,
                'flood_resilience_score': 50,
                'healthcare_access_score': 50,
                'green_space_score': 50,
                'overall_resilience_score': 50
            }
            
            # Air Quality Score (0-100, higher is better)
            # Adjusted for Indian cities where AQI 100-300 is common
            if 'ward_air_quality' in analysis_results:
                ward_air = analysis_results['ward_air_quality']
                if not ward_air.empty:
                    avg_aqi = ward_air['mean_aqi'].mean()
                    # More realistic scoring for Indian cities:
                    # AQI 0-50: Score 100 (Excellent)
                    # AQI 51-100: Score 80 (Good) 
                    # AQI 101-200: Score 50 (Moderate)
                    # AQI 201-300: Score 20 (Poor)
                    # AQI 301+: Score 0 (Very Poor)
                    if avg_aqi <= 50:
                        scores['air_quality_score'] = 100
                    elif avg_aqi <= 100:
                        scores['air_quality_score'] = 100 - (avg_aqi - 50)  # 100 to 50
                    elif avg_aqi <= 200:
                        scores['air_quality_score'] = 50 - (avg_aqi - 100) * 0.3  # 50 to 20
                    elif avg_aqi <= 300:
                        scores['air_quality_score'] = 20 - (avg_aqi - 200) * 0.2  # 20 to 0
                    else:
                        scores['air_quality_score'] = 0
                    
                    scores['air_quality_score'] = max(0, scores['air_quality_score'])
                    logger.info(f"🌬️  Air Quality: AQI {avg_aqi:.1f} → Score {scores['air_quality_score']:.1f}/100")
            
            # Heat Resilience Score (based on real MODIS data)
            if 'heat_islands' in analysis_results:
                heat_islands = analysis_results['heat_islands']
                if not heat_islands.empty:
                    # Score based on heat island intensity and coverage
                    total_area = len(heat_islands)
                    if total_area > 0:
                        # More heat islands = lower resilience score
                        heat_coverage = min(total_area / 1000, 1.0)  # Normalize by expected max
                        scores['heat_resilience_score'] = max(0, 100 - (heat_coverage * 80))
                        logger.info(f"🌡️  Heat Resilience: {total_area} heat islands → Score {scores['heat_resilience_score']:.1f}/100")
            
            # Healthcare Access Score (based on real healthcare gaps)
            if 'healthcare_gaps' in analysis_results:
                health_gaps = analysis_results['healthcare_gaps']
                if not health_gaps.empty:
                    # Score based on healthcare gap severity
                    critical_gaps = len(health_gaps[health_gaps['priority'] == 'Critical'])
                    total_gaps = len(health_gaps)
                    if total_gaps > 0:
                        gap_ratio = critical_gaps / total_gaps
                        scores['healthcare_access_score'] = max(0, 100 - (gap_ratio * 100))
                        logger.info(f"🏥 Healthcare Access: {critical_gaps}/{total_gaps} critical gaps → Score {scores['healthcare_access_score']:.1f}/100")
            elif 'healthcare_capacity' in analysis_results:
                health_cap = analysis_results['healthcare_capacity']
                if not health_cap.empty:
                    avg_facilities_per_1000 = health_cap['facilities_per_1000'].mean()
                    scores['healthcare_access_score'] = min(100, avg_facilities_per_1000 * 100)
            
            # Green Space Score (based on real vegetation analysis)
            if 'green_space_deficits' in analysis_results:
                green_def = analysis_results['green_space_deficits']
                if not green_def.empty:
                    avg_green_score = green_def['combined_green_score'].mean()
                    scores['green_space_score'] = avg_green_score
                    logger.info(f"🌳 Green Space: Average score {avg_green_score:.1f} → Score {scores['green_space_score']:.1f}/100")
            
            # Flood Resilience Score (based on real flood zones analysis)
            if 'flood_zones' in analysis_results:
                flood_zones = analysis_results['flood_zones']
                if not flood_zones.empty:
                    high_risk_zones = len(flood_zones[flood_zones['flood_risk_score'] >= 0.5])
                    total_zones = len(flood_zones)
                    if total_zones > 0:
                        risk_ratio = high_risk_zones / total_zones
                        scores['flood_resilience_score'] = max(0, 100 - (risk_ratio * 80))
                        logger.info(f"🌊 Flood Resilience: {high_risk_zones}/{total_zones} high-risk zones → Score {scores['flood_resilience_score']:.1f}/100")
            elif 'drainage_analysis' in analysis_results:
                drainage_data = analysis_results['drainage_analysis']
                if not drainage_data.empty:
                    avg_flood_risk = drainage_data['avg_flood_risk'].mean()
                    scores['flood_resilience_score'] = max(0, 100 - (avg_flood_risk * 100))
                    logger.info(f"🌊 Flood Resilience: Average risk {avg_flood_risk:.2f} → Score {scores['flood_resilience_score']:.1f}/100")
            
            # Calculate overall score
            scores['overall_resilience_score'] = np.mean(list(scores.values())[:-1])
            
            # Add recommendation statistics
            total_cost = sum(rec.estimated_cost_usd for rec in recommendations)
            critical_recs = len([rec for rec in recommendations if rec.priority == Priority.CRITICAL])
            high_recs = len([rec for rec in recommendations if rec.priority == Priority.HIGH])
            medium_recs = len([rec for rec in recommendations if rec.priority == Priority.MEDIUM])
            low_recs = len([rec for rec in recommendations if rec.priority == Priority.LOW])
            
            result = {
                'resilience_scores': scores,
                'recommendations_summary': {
                    'total_recommendations': len(recommendations),
                    'critical_priority': critical_recs,
                    'high_priority': high_recs,
                    'medium_priority': medium_recs,
                    'low_priority': low_recs,
                    'total_estimated_cost_usd': total_cost,
                    'avg_cost_per_recommendation': total_cost / len(recommendations) if recommendations else 0
                },
                'city_status': self._determine_city_status(scores['overall_resilience_score'])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating resilience score: {e}")
            return {'resilience_scores': {'overall_resilience_score': 50}}
    
    def _determine_city_status(self, overall_score: float) -> str:
        """Determine city resilience status based on score."""
        if overall_score >= 80:
            return "Highly Resilient"
        elif overall_score >= 65:
            return "Moderately Resilient"
        elif overall_score >= 50:
            return "Developing Resilience"
        elif overall_score >= 35:
            return "Vulnerable"
        else:
            return "Highly Vulnerable"
