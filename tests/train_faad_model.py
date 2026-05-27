import pickle
import numpy as np
from sklearn.ensemble import IsolationForest

def main():
    print("[Train] Generating normal baseline telemetry data...")
    # Generate 1000 normal telemetry samples
    # Temperature: normal mean 50C, std 5C
    # Speed: normal mean 100 km/h, std 10 km/h
    # Charge Level: normal mean 75%, std 5%
    np.random.seed(42)
    temp = np.random.normal(50, 5, 1000)
    speed = np.random.normal(100, 10, 1000)
    charge = np.random.normal(75, 5, 1000)
    
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
    
    import os
    dir_path = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(dir_path, "faad_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model_data, f)
        
    print(f"[Train] Model successfully saved to {model_path}")
    print(f"  Means: Temp={means[0]:.2f}, Speed={means[1]:.2f}, Charge={means[2]:.2f}")
    print(f"  Stds:  Temp={stds[0]:.2f}, Speed={stds[1]:.2f}, Charge={stds[2]:.2f}")

if __name__ == "__main__":
    main()
