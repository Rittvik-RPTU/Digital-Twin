import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import os

# Import our data generator to ensure dataset is ready
from data_generator import generate_telemetry_data

def main():
    print("[Train] Loading training telemetry data from UCI dataset...")
    df = generate_telemetry_data()
    
    # Filter for the training split (which contains normal baseline data)
    train_df = df[df['split'] == 'Train']
    
    temp = train_df['airTemperature'].values
    speed = train_df['rotationalSpeed'].values
    charge = train_df['torque'].values
    
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
            "airTemperature": means[0],
            "rotationalSpeed": means[1],
            "torque": means[2]
        },
        "stds": {
            "airTemperature": stds[0],
            "rotationalSpeed": stds[1],
            "torque": stds[2]
        }
    }
    
    dir_path = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(dir_path, "faad_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model_data, f)
        
    print(f"[Train] Model successfully saved to {model_path}")
    print(f"  Means: AirTemp={means[0]:.2f}, RotSpeed={means[1]:.2f}, Torque={means[2]:.2f}")
    print(f"  Stds:  AirTemp={stds[0]:.2f}, RotSpeed={stds[1]:.2f}, Torque={stds[2]:.2f}")

if __name__ == "__main__":
    main()
