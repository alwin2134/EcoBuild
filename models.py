from pydantic import BaseModel
from typing import Optional, Dict

class UserInput(BaseModel):
    # Location (Simple)
    city: str
    project_type: str = "Residential" # Dropdown support
    
    # Project Specs
    land_area_m2: float
    built_up_area_m2: float
    floors: int
    
    # Resources
    daily_water_m3: float
    daily_waste_kg: float
    hazardous_waste_kg_per_month: float
    
    # Activity
    vehicles_per_day: int
    fuel_consumption_l_per_day: float
    dg_hours_per_day: float
    
    # Context (Can keep these or make optional, let's keep for now)
    distance_to_residential_m: float
    distance_to_water_body_km: float
    # Defaults/Optionals (User doesn't input these)
    vegetation_removed_percent: float = 0.0
    
    # Green Features
    green_area_percent: float = 0.0
    has_rainwater_harvesting: int = 0
    has_solar: int = 0
    energy_efficient_lighting: int = 0
    waste_segregation: int = 0
    stp_present: int = 0
    
class EnrichedProjectInput(BaseModel):
    # Inherits everything from UserInput logic basically, but flat structure is easier for ML
    
    # Copy of UserInput
    land_area_m2: float
    built_up_area_m2: float
    floors: int
    daily_water_m3: float
    daily_waste_kg: float
    hazardous_waste_kg_per_month: float
    vehicles_per_day: int
    fuel_consumption_l_per_day: float
    distance_to_residential_m: float
    vegetation_removed_percent: float
    avg_noise_db: float # Derived/Default
    near_sensitive_zone: int # Derived from Lat/Lng check
    
    # Environmental Baseline (Lookup)
    baseline_pm25: float
    baseline_no2: float
    baseline_so2: float
    baseline_co: float
    baseline_o3: float 
    
    # For calculation
    dg_hours_per_day: float
    distance_to_water_body_km: float
    stp_present: int
    has_rainwater_harvesting: int
    waste_segregation: int
    green_area_percent: int
    has_solar: int
    energy_efficient_lighting: int
    
    # Additional fields needed for logic
    built_up_area_m2: float # Already there but good to be explicit
    rooms: int = 1 # Added fallback as it was used in calculation but missing here
    has_rainwater_harvesting: int = 0
    has_solar: int = 0
    energy_efficient_lighting: int = 0
    waste_segregation: int = 0
    stp_present: int = 0

class ImpactResult(BaseModel):
    overall_score: float
    impact_class: str
    breakdown: Dict[str, float]
    # Detailed pollution
    added_pollution: Dict[str, float]
    final_pollution: Dict[str, float]
    recommendations: list[str]

class MLPrediction(BaseModel):
    predicted_class: int
    label: str
    confidence: float

class BlueprintResult(BaseModel):
    success: bool
    data: Optional[Dict]
    message: str
