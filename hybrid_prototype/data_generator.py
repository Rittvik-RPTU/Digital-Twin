import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_telemetry_data(num_samples=500, randomize=False):
    """
    Generates synthetic telemetry data for the Digital Twin FAAD prototype.
    Contains three phases:
    1. Normal behavior (Correlated speed and temperature)
    2. Statistical Spike (Sudden temperature jump)
    3. Contextual Anomaly (High temperature while speed is zero)
    """
    if randomize:
        np.random.seed(None)
    else:
        np.random.seed(42)
    
    # Initialize arrays
    time_steps = np.arange(num_samples)
    speed = np.zeros(num_samples)
    temperature = np.zeros(num_samples)
    labels = np.array(['Normal'] * num_samples, dtype=object)

    # ---------------------------------------------------------
    # Phase 1: Normal Baseline (0 to 200)
    # Speed fluctuates around 60 km/h, Temp is correlated.
    # ---------------------------------------------------------
    speed[0:200] = 60 + np.sin(time_steps[0:200] / 10) * 10 + np.random.normal(0, 2, 200)
    temperature[0:200] = 40 + (speed[0:200] * 0.3) + np.random.normal(0, 1.5, 200)

    # ---------------------------------------------------------
    # Phase 2: Statistical Spike (200 to 250)
    # Target for Z-Score: Sudden huge spike in temperature.
    # ---------------------------------------------------------
    speed[200:250] = 60 + np.random.normal(0, 2, 50)
    temperature[200:250] = 40 + (speed[200:250] * 0.3) + np.random.normal(0, 1.5, 50)
    
    # Inject the spike right in the middle
    temperature[225] = 115.0 # Sharp spike, still under 120 (Layer A hard bound)
    temperature[226] = 110.0
    labels[225:227] = 'Statistical Anomaly'

    # ---------------------------------------------------------
    # Phase 3: Return to Normal (250 to 350)
    # ---------------------------------------------------------
    speed[250:350] = 80 + np.sin(time_steps[250:350] / 10) * 15 + np.random.normal(0, 2, 100)
    temperature[250:350] = 40 + (speed[250:350] * 0.3) + np.random.normal(0, 1.5, 100)

    # ---------------------------------------------------------
    # Phase 4: Contextual Anomaly (350 to 400)
    # Target for Isolation Forest: Speed drops to 0, but temp stays very high
    # ---------------------------------------------------------
    speed[350:400] = np.random.normal(0, 0.5, 50) # Basically parked
    speed[speed < 0] = 0 # Can't have negative speed
    temperature[350:400] = 95 + np.random.normal(0, 2, 50) # High temperature
    labels[350:400] = 'Contextual Anomaly'

    # ---------------------------------------------------------
    # Phase 5: Return to Normal (400 to 500)
    # ---------------------------------------------------------
    speed[400:500] = 50 + np.sin(time_steps[400:500] / 10) * 10 + np.random.normal(0, 2, 100)
    temperature[400:500] = 40 + (speed[400:500] * 0.3) + np.random.normal(0, 1.5, 100)

    # Add split column to indicate which rows are used for training
    split = ['Train'] * 150 + ['Test'] * (num_samples - 150)

    # Combine into DataFrame
    df = pd.DataFrame({
        'time': time_steps,
        'speed': speed,
        'temperature': temperature,
        'label': labels,
        'split': split
    })
    
    return df

def plot_dataset(df, save_path="dataset_overview.png"):
    plt.figure(figsize=(14, 6))
    
    # Plot Speed
    plt.plot(df['time'], df['speed'], label='Speed (km/h)', color='blue', alpha=0.6)
    
    # Plot Temperature
    plt.plot(df['time'], df['temperature'], label='Temperature (°C)', color='red', alpha=0.8)
    
    # Highlight Statistical Anomalies
    stat_anomalies = df[df['label'] == 'Statistical Anomaly']
    plt.scatter(stat_anomalies['time'], stat_anomalies['temperature'], color='black', marker='x', s=100, label='Statistical Spike (Z-Score Target)')
    
    # Highlight Contextual Anomalies
    ctx_anomalies = df[df['label'] == 'Contextual Anomaly']
    plt.scatter(ctx_anomalies['time'], ctx_anomalies['temperature'], color='purple', marker='o', s=30, label='Contextual Drift (IF Target)')

    plt.axhline(y=120, color='red', linestyle='--', alpha=0.5, label='Hard Bound (Layer A)')
    
    plt.title('Synthetic Telemetry Dataset for FAAD Prototype')
    plt.xlabel('Time Steps')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Plot saved to {save_path}")

if __name__ == "__main__":
    print("Generating synthetic dataset...")
    dataset = generate_telemetry_data()
    
    # Save to CSV
    csv_path = "telemetry_dataset.csv"
    dataset.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path} ({len(dataset)} records).")
    
    # Generate Plot
    plot_dataset(dataset)
