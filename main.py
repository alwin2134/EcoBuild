from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import joblib
import shutil
import os
from math import radians, cos, sin, asin, sqrt

# Import local modules
from models import UserInput, EnrichedProjectInput, ImpactResult, MLPrediction, BlueprintResult
from blueprint_utils import analyze_blueprint

from fastapi.responses import FileResponse

# Force Reload for Model Update

app = FastAPI(title="EIA EcoBuild Engine")

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load Resources
try:
    ML_MODEL = joblib.load('impact_model.pkl')
    SENSITIVE_LOCS = pd.read_csv('data/sensitive_locations.csv')
    CITIES_DB = pd.read_csv('data/cities_aqi.csv')
    # Normalize city names for easier lookup
    CITIES_DB['city_lower'] = CITIES_DB['city'].str.lower()
    print("Resources loaded successfully.")
except Exception as e:
    print(f"Warning: Resources not loaded: {e}")
    ML_MODEL = None
    SENSITIVE_LOCS = None
    CITIES_DB = None

@app.get("/api/health")
def health_check():
    return {"status": "online", "system": "EIA EcoBuild Engine"}

@app.get("/")
async def read_root():
    return FileResponse('EcoBuild.html')

# --- UTILS ---
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in km between two points 
    on the earth (specified in decimal degrees)
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

def enrich_data(user_input: UserInput) -> EnrichedProjectInput:
    """
    Transforms simple user input into full technical input by looking up city data.
    """
    # Default fallback (Median of dataset approx)
    defaults = {
        "pm25": 100.0, "no2": 40.0, "so2": 15.0, "co": 1.5, "o3": 30.0, 
        "lat": 20.5937, "lng": 78.9629, "noise": 55.0
    }
    
    city_key = user_input.city.lower().strip()
    city_data = None
    
    if CITIES_DB is not None:
        match = CITIES_DB[CITIES_DB['city_lower'] == city_key]
        if not match.empty:
            city_data = match.iloc[0]
            
    # Enrich
    lat = city_data['latitude'] if city_data is not None else defaults['lat']
    lng = city_data['longitude'] if city_data is not None else defaults['lng']

    # Proximity Check (Simplified: Check if City Center is near any Sensitive Zone)
    # Ideally we'd need exact project location, but for MVP city center is the proxy.
    near_sensitive = 0
    if SENSITIVE_LOCS is not None:
        for _, row in SENSITIVE_LOCS.iterrows():
            dist = haversine(lng, lat, row['lng'], row['lat'])
            if dist < 5.0: # 5km Buffer
                near_sensitive = 1
                break
                
    # Noise Estimation based on Type
    base_noise = 50.0
    if user_input.project_type == "Industrial": base_noise = 75.0
    elif user_input.project_type == "Commercial": base_noise = 65.0
    
    return EnrichedProjectInput(
        land_area_m2=user_input.land_area_m2,
        built_up_area_m2=user_input.built_up_area_m2,
        floors=user_input.floors,
        daily_water_m3=user_input.daily_water_m3,
        daily_waste_kg=user_input.daily_waste_kg,
        hazardous_waste_kg_per_month=user_input.hazardous_waste_kg_per_month,
        vehicles_per_day=user_input.vehicles_per_day,
        fuel_consumption_l_per_day=user_input.fuel_consumption_l_per_day,
        distance_to_residential_m=user_input.distance_to_residential_m,
        vegetation_removed_percent=user_input.vegetation_removed_percent,
        avg_noise_db=base_noise,
        near_sensitive_zone=near_sensitive,
        
        # Environmental Baseline
        baseline_pm25=float(city_data['pm25']) if city_data is not None else defaults['pm25'],
        baseline_no2=float(city_data['no2']) if city_data is not None else defaults['no2'],
        baseline_so2=float(city_data['so2']) if city_data is not None else defaults['so2'],
        baseline_co=float(city_data['co_mg_m3']) if city_data is not None else defaults['co'],
        baseline_o3=float(city_data['o3']) if city_data is not None else defaults['o3'],
        
        # Passthrough / Calc Props
        dg_hours_per_day=user_input.dg_hours_per_day,
        distance_to_water_body_km=user_input.distance_to_water_body_km,
        stp_present=user_input.stp_present,
        has_rainwater_harvesting=user_input.has_rainwater_harvesting,
        waste_segregation=user_input.waste_segregation,
        green_area_percent=int(user_input.green_area_percent),
        has_solar=user_input.has_solar,
        energy_efficient_lighting=user_input.energy_efficient_lighting
    )

# --- ENDPOINTS ---

@app.post("/analyze-blueprint", response_model=BlueprintResult)
async def upload_blueprint(file: UploadFile = File(...)):
    if file.filename.lower().endswith('.dwg'):
         return {
            "success": False, 
            "data": None, 
            "message": "DWG files are binary and not supported. Please convert to .DXF using a CAD tool (or online converter) and upload."
        }

    if not file.filename.endswith(('.dxf', '.DXF')):
         return {
            "success": False, 
            "data": None, 
            "message": "Only .DXF files are supported for Blueprint Analysis in this version."
        }
    
    # Use system temp directory to avoid triggering reloads (Uvicorn/LiveServer)
    import tempfile
    
    # Create a temp file with .dxf suffix so ezdxf can read it if extension matters (though usually reads content)
    # delete=False because we need to close it before ezdxf re-opens it on Windows
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name
        
    try:
        result = analyze_blueprint(temp_path)
        os.remove(temp_path) # Cleanup
        return {"success": result['success'], "data": result, "message": result.get('message', 'Analyzed')}
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"success": False, "data": None, "message": str(e)}

@app.post("/calculate-impact", response_model=ImpactResult)
def calculate_impact(user_data: UserInput):
    # Lookup Data
    data = enrich_data(user_data)
    
    # 1. Physics Engine (Simplified)
    # Added Pollution
    added_pm25 = ((data.vehicles_per_day * 0.5) + (data.fuel_consumption_l_per_day * 2)) / 1000 # kg/day approx scaled
    added_no2 = ((data.vehicles_per_day * 0.2) + (data.fuel_consumption_l_per_day * 20)) / 1000
    
    # Construction Dust
    construction_dust = data.built_up_area_m2 * 0.0001 * (1 + (data.vegetation_removed_percent/100))
    
    # Final Concentrations (Box Model coeff = 50 for local)
    final_pm25 = data.baseline_pm25 + (added_pm25 * 50)
    final_no2 = data.baseline_no2 + (added_no2 * 50)
    
    # 2. Rule-Based Scoring (Lower is Better for Environment, but we want Score out of 100)
    # Let's verify scoring: "Impact Score". High Impact = High Score.
    # User Requirement: <=30 Low, 60+ High. So 0 is Good, 100 is Bad.
    
    # Air Score (0-100)
    # AQI > 300 is bad. 
    air_score = (final_pm25 / 250 * 50) + (final_no2 / 100 * 30) + (data.dg_hours_per_day * 2)
    air_score = min(100, air_score)
    
    # Water Score
    # 135 LPCD is standard.
    # Total liters = data.daily_water_m3 * 1000
    # Persons approx = rooms * 2
    # Fix: 'rooms' is not in EnrichedInput, let's derive approx occupancy from water or area
    # 10 sq m per person?
    persons = max(1, data.built_up_area_m2 / 15) 
    lpcd = (data.daily_water_m3 * 1000) / persons
    
    water_score = 0
    if lpcd > 150: water_score += 40
    if data.distance_to_water_body_km < 0.5: water_score += 40
    if data.stp_present == 0: water_score += 20
    if data.has_rainwater_harvesting == 1: water_score -= 10
    water_score = max(0, min(100, water_score))
    
    # Waste Score
    waste_score = (data.daily_waste_kg / 100 * 10) + (data.hazardous_waste_kg_per_month * 2)
    if data.waste_segregation == 0: waste_score += 20
    waste_score = min(100, waste_score)
    
    # Land/Bio Score
    land_score = (data.vegetation_removed_percent) 
    if data.near_sensitive_zone == 1: land_score += 40
    if data.green_area_percent < 10: land_score += 20
    land_score = min(100, land_score)
    
    # Noise Score
    noise_score = data.avg_noise_db - 45 # Baseline silence
    noise_score = max(0, noise_score * 2)
    if data.distance_to_residential_m < 50: noise_score += 20
    noise_score = min(100, noise_score)
    
    # Overall Score (Weighted)
    # Weights: Air 30%, Water 25%, Land 20%, Waste 15%, Noise 10%
    overall_score = (air_score * 0.3) + (water_score * 0.25) + (land_score * 0.2) + (waste_score * 0.15) + (noise_score * 0.10)
    
    # Recommendations
    recs = []
    if air_score > 50: recs.append("High Air Pollution risk: Install Air Purifiers and Smog Towers.")
    if water_score > 50: recs.append("Critical Water usage: Mandate STP and Rainwater Harvesting.")
    if land_score > 50: recs.append("High ecological impact: Increase Green Belt area > 30%.")
    if data.has_solar == 0: recs.append("Energy: Install Solar Panels to reduce carbon footprint.")
    if data.energy_efficient_lighting == 0: recs.append("Energy: Switch to LED lighting.")

    # Class
    imp_class = "Low"
    if overall_score > 60: imp_class = "High"
    elif overall_score > 30: imp_class = "Moderate"

    return {
        "overall_score": round(overall_score, 1),
        "impact_class": imp_class,
        "breakdown": {
            "Air Impact": round(air_score, 1),
            "Water Impact": round(water_score, 1),
            "Land Impact": round(land_score, 1),
            "Waste Impact": round(waste_score, 1),
            "Noise Impact": round(noise_score, 1)
        },
        "added_pollution": {
            "PM2.5": round(added_pm25, 4),
            "NO2": round(added_no2, 4)
        },
        "final_pollution": {
            "PM2.5": round(final_pm25, 2),
            "NO2": round(final_no2, 2)
        },
        "recommendations": recs
    }

@app.post("/predict-impact-ml", response_model=MLPrediction)
def predict_impact_ml(user_data: UserInput):
    if ML_MODEL is None:
        raise HTTPException(status_code=503, detail="ML Model not loaded")
    
    # Lookup
    data = enrich_data(user_data)
    
    # Feature Engineering (Same as ml_train logic)
     # Added Pollution (Replicated logic)
    added_pm25 = ((data.vehicles_per_day * 0.5) + (data.fuel_consumption_l_per_day * 2)) / 1000 
    added_no2 = ((data.vehicles_per_day * 0.2) + (data.fuel_consumption_l_per_day * 20)) / 1000
    construction_dust = data.built_up_area_m2 * 0.0001 * (1 + (data.vegetation_removed_percent/100))
    final_pm25 = data.baseline_pm25 + (added_pm25 * 50)
    final_no2 = data.baseline_no2 + (added_no2 * 50)
    
    # Fill remaining physics variables with defaults for ML stability if needed, simplified here:
    final_so2 = data.baseline_so2 
    final_co = data.baseline_co
    
    # Feature Vector
    # Must match training order:
    # 'land_area_m2', 'built_up_area_m2', 'floors', 'daily_water_m3', 
    # 'daily_waste_kg', 'hazardous_waste_kg_per_month', 'avg_noise_db', 
    # 'distance_to_residential_m', 'vegetation_removed_percent', 
    # 'near_sensitive_zone', 'vehicles_per_day', 'fuel_consumption_l_per_day',
    # 'final_pm25', 'final_no2', 'final_so2', 'final_co'
    
    features = [[
        data.land_area_m2, data.built_up_area_m2, data.floors, data.daily_water_m3,
        data.daily_waste_kg, data.hazardous_waste_kg_per_month, data.avg_noise_db,
        data.distance_to_residential_m, data.vegetation_removed_percent,
        data.near_sensitive_zone, data.vehicles_per_day, data.fuel_consumption_l_per_day,
        final_pm25, final_no2, final_so2, final_co
    ]]
    
    pred_class = ML_MODEL.predict(features)[0]
    probs = ML_MODEL.predict_proba(features)[0]
    confidence = max(probs)
    
    labels = {0: "Low", 1: "Moderate", 2: "High"}
    
    return {
        "predicted_class": int(pred_class),
        "label": labels.get(int(pred_class), "Unknown"),
        "confidence": round(float(confidence) * 100, 2)
    }

@app.get("/analyze-location")
def analyze_location_proximity(city: str):
    # Just return City Center info + Nearest sensitive zone to city center
    if CITIES_DB is None: return {"nearest_location": "Unknown", "distance_km": 0, "risk": "Unknown"}
    
    match = CITIES_DB[CITIES_DB['city_lower'] == city.lower()]
    if match.empty:
         return {"nearest_location": "City Not Found", "distance_km": 0, "risk": "Unknown"}
         
    city_data = match.iloc[0]
    lat, lng = city_data['latitude'], city_data['longitude']
    
    if SENSITIVE_LOCS is None:
          return {"nearest_location": "Unknown", "distance_km": 0, "risk": "Unknown"}
    
    min_dist = float('inf')
    nearest = None
    
    for idx, row in SENSITIVE_LOCS.iterrows():
        dist = haversine(lng, lat, row['lng'], row['lat'])
        if dist < min_dist:
            min_dist = dist
            nearest = row
            
    risk = "Low"
    if min_dist < 2.0: risk = "High"
    elif min_dist < 10.0: risk = "Moderate" # Larger buffer for city-level
    
    return {
        "nearest_location": nearest['name'],
        "type": nearest['category'],
        "distance_km": round(min_dist, 2),
        "risk": risk
    }

# Serve Frontend (Must be last to avoid shadowing API routes)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
