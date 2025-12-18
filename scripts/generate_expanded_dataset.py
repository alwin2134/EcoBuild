import pandas as pd
import numpy as np

def run_data_expansion():
    # Load Datasets
    projects = pd.read_csv('data/sample_projects.csv')
    cities = pd.read_csv('data/cities_aqi.csv')

    # Merge AQI baseline data
    expanded = pd.merge(projects, cities, on="city", how="left")

    # Estimation Logic for Added Pollution (Simple Physics/Empirical based approximation)
    # 1. Vehicle Emissions
    # Avg emission factor per vehicle km (approx): NO2: 0.2g, PM2.5: 0.05g, CO: 2.0g
    # Assumed avg trip length 10km
    
    expanded['added_pm25'] = (expanded['vehicles_per_day'] * 10 * 0.05) / 1000  # kg/day
    expanded['added_no2'] = (expanded['vehicles_per_day'] * 10 * 0.2) / 1000
    expanded['added_co'] = (expanded['vehicles_per_day'] * 10 * 2.0) / 1000

    # 2. DG Set (Fuel Consumption)
    # Diesel emission: PM: 2g/L, NOx: 20g/L, SO2: 4g/L, CO: 5g/L
    expanded['dg_pm25'] = (expanded['fuel_consumption_l_per_day'] * 2) / 1000
    expanded['dg_no2'] = (expanded['fuel_consumption_l_per_day'] * 20) / 1000
    expanded['dg_so2'] = (expanded['fuel_consumption_l_per_day'] * 4) / 1000
    expanded['dg_co'] = (expanded['fuel_consumption_l_per_day'] * 5) / 1000

    # 3. Construction Dust (Based on built-up area)
    # Approx 0.1g per m2 per day if not mitigated. Impact reduced by vegetation.
    # Mitigation factor: vegetation_removed_percent (higher removal = more dust)
    dust_base = expanded['built_up_area_m2'] * 0.0001
    dust_factor = 1 + (expanded['vegetation_removed_percent'] / 100)
    expanded['construction_pm10'] = dust_base * dust_factor

    # Convert Emissions (kg/day) to Concentration Impact (µg/m3)
    # This assumes a "Box Model" dispersion over the project area + buffer
    # Simplified: Impact = Emission / (Area * MixHeight * WindSpeed)
    # We will use a simplified coefficient for "Project Local Impact"
    dispersion_factor = 100 # Arbitrary physics mock constant for this scope
    
    expanded['final_pm25'] = expanded['pm25'] + ((expanded['added_pm25'] + expanded['dg_pm25']) * dispersion_factor)
    expanded['final_pm10'] = expanded['pm10'] + (expanded['construction_pm10'] * dispersion_factor)
    expanded['final_no2'] = expanded['no2'] + ((expanded['added_no2'] + expanded['dg_no2']) * dispersion_factor)
    expanded['final_so2'] = expanded['so2'] + (expanded['dg_so2'] * dispersion_factor)
    expanded['final_co'] = expanded['co_mg_m3'] + ((expanded['added_co'] + expanded['dg_co']) * 0.1) # CO is mg/m3

    # Save
    expanded.to_csv('data/expanded_eia_dataset.csv', index=False)
    print("MetaData: Expanded dataset generated with derived pollution metrics.")
    print(f"Rows: {len(expanded)}")

if __name__ == "__main__":
    run_data_expansion()
