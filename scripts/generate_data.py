import pandas as pd
import numpy as np
import random

def generate_synthetic_data(n=5000):
    # Seed for reproducibility
    np.random.seed(42)
    
    data = []
    
    cities = ['Delhi', 'Mumbai', 'Bengaluru', 'Chennai', 'Hyderabad', 
              'Kolkata', 'Pune', 'Ahmedabad', 'Noida', 'Gurugram']
    
    types = ['Residential', 'Commercial', 'Industrial']
    
    for _ in range(n):
        # 1. Random Inputs within realistic ranges
        city = random.choice(cities)
        p_type = random.choice(types)
        
        # Base multipliers
        size_mult = 1.0
        if p_type == 'Commercial': size_mult = 1.5
        if p_type == 'Industrial': size_mult = 2.0
        
        land_area = int(np.random.normal(5000 * size_mult, 2000))
        land_area = max(500, land_area)
        
        built_up = int(land_area * np.random.uniform(1.5, 4.0)) # FSI
        
        floors = max(1, int(built_up / land_area * 1.2))
        
        # Resource consumption
        water = built_up * 0.005 * np.random.uniform(0.8, 1.2)
        waste = built_up * 0.002 * np.random.uniform(0.8, 1.2)
        haz_waste = 0
        if p_type == 'Industrial':
            haz_waste = waste * 0.1 * np.random.uniform(0.5, 2.0)
            
        # Traffic
        vehicles = int(built_up * 0.05 * np.random.uniform(0.5, 1.5))
        fuel = vehicles * 0.5
        
        # Context
        dist_res = np.random.randint(50, 1000)
        veg_removed = np.random.uniform(0, 100)
        sensitive = 1 if np.random.random() < 0.1 else 0
        
        # --- CALCULATE "TRUE" IMPACT SCORE (The Target) ---
        # We use a formula similar to our backend rule engine to label the data
        # so the ML model learns to mimic this logic perfectly.
        
        score = 0
        
        # 1. Resource Intensity
        if water > 1000: score += 15
        elif water > 100: score += 10
        else: score += 5
        
        if waste > 500: score += 15
        elif waste > 50: score += 10
        else: score += 5
        
        if haz_waste > 50: score += 20 # Penalize Industrial
        
        # 2. Traffic
        if vehicles > 500: score += 15
        
        # 3. Location Sensitivity
        if sensitive: score += 25
        if dist_res < 100: score += 10
        if veg_removed > 50: score += 10
        
        # 4. Add Random Noise to Score (to make it realistic/harder)
        noise = np.random.randint(-5, 5)
        final_score = max(0, min(100, score + noise))
        
        # 5. Determine Class Labels
        # Low < 40, Moderate 40-70, High > 70
        if final_score < 40:
            impact_class = 0 # Low
            label = 'Low'
        elif final_score < 70:
            impact_class = 1 # Moderate
            label = 'Moderate'
        else:
            impact_class = 2 # High
            label = 'High'
            
        # 6. Final Outputs (mocking the "final_pollution" derived features)
        # In a real pipeline, these would be calculated. Here we simulate them correlated to input.
        pm25 = 50 + (vehicles * 0.1) + (waste * 0.05)
        no2 = 20 + (vehicles * 0.05)
        
        row = {
            'land_area_m2': land_area,
            'built_up_area_m2': built_up,
            'floors': floors,
            'daily_water_m3': water,
            'daily_waste_kg': waste,
            'hazardous_waste_kg_per_month': haz_waste,
            'avg_noise_db': np.random.uniform(40, 90),
            'distance_to_residential_m': dist_res,
            'vegetation_removed_percent': veg_removed,
            'near_sensitive_zone': sensitive,
            'vehicles_per_day': vehicles,
            'fuel_consumption_l_per_day': fuel,
            'final_pm25': pm25,
            'final_no2': no2,
            'final_so2': pm25 * 0.1,
            'final_co': pm25 * 0.01,
            'impact_class_numeric': impact_class,
            'impact_label': label 
        }
        data.append(row)
        
    df = pd.DataFrame(data)
    df.to_csv('data/synthetic_eia_data.csv', index=False)
    print(f"Generated {n} synthetic samples to data/synthetic_eia_data.csv")

if __name__ == "__main__":
    generate_synthetic_data()
