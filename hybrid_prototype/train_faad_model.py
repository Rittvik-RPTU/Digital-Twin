import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import os

# Import our data generator to ensure dataset is ready
from data_generator import generate_telemetry_data

def main():
    print("[Train] Loading training telemetry data from Stanford EV dataset...")
    df = generate_telemetry_data()
    
    # Filter for the training split (which contains normal baseline data)
    train_df = df[df['split'] == 'Train']
    
    temp = train_df['temperature'].values
    speed = train_df['speed'].values
    charge = train_df['chargeLevel'].values
    
    X_train = np.column_stack((temp, speed, charge))
    
    # Train Isolation Forest
    print("[Train] Training Isolation Forest estimator...")
    clf = IsolationForest(contamination=0.01, random_state=42)
    clf.fit(X_train)
    
    # Calculate Z-Score parameters
    means = np.mean(X_train, axis=0)
    stds = np.std(X_train, axis=0)
    
    # Pack model data
    model_data = {
        "isolation_forest": clf,
        "means": {
            "temperature": means[0],
            "speed": means[1],
            "chargeLevel": means[2]
        },
        "stds": {
            "temperature": stds[0],
            "speed": stds[1],
            "chargeLevel": stds[2]
        }
    }
    
    dir_path = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(dir_path, "faad_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model_data, f)
        
    print(f"[Train] Model successfully saved to {model_path}")
    print(f"  Means: Temp={means[0]:.2f}, Speed={means[1]:.2f}, Charge={means[2]:.2f}")
    print(f"  Stds:  Temp={stds[0]:.2f}, Speed={stds[1]:.2f}, Charge={stds[2]:.2f}")

if __name__ == "__main__":
    main()
