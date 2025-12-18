import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def train_model():
    # Load High-Quality Synthetic Data
    df = pd.read_csv('data/synthetic_eia_data.csv')
    
    # Features
    features = [
        'land_area_m2', 'built_up_area_m2', 'floors', 'daily_water_m3', 
        'daily_waste_kg', 'hazardous_waste_kg_per_month', 'avg_noise_db', 
        'distance_to_residential_m', 'vegetation_removed_percent', 
        'near_sensitive_zone', 'vehicles_per_day', 'fuel_consumption_l_per_day',
        'final_pm25', 'final_no2', 'final_so2', 'final_co'
    ]
    
    X = df[features].fillna(0)
    y = df['impact_class_numeric']

    # Train
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    print("Model Evaluation:")
    print(classification_report(y_test, clf.predict(X_test)))

    # Save
    joblib.dump(clf, 'impact_model.pkl')
    print("Model saved to impact_model.pkl")

if __name__ == "__main__":
    train_model()
