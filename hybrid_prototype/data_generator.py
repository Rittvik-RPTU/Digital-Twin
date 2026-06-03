import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import urllib.request

DATA_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv"
CACHE_FILE = "ai4i2020.csv"

def download_dataset():
    """Downloads the UCI AI4I 2020 Predictive Maintenance Dataset if not cached."""
    if not os.path.exists(CACHE_FILE):
        print(f"Downloading dataset from {DATA_URL}...")
        urllib.request.urlretrieve(DATA_URL, CACHE_FILE)
        print("Download complete.")
    else:
        print("Using cached dataset.")

def generate_telemetry_data(num_samples=1000, randomize=False):
    """
    Ingests 1,000 rows of the UCI AI4I 2020 dataset and maps its physical telemetry.
    - Training set: First 500 rows (split = 'Train' where failure == 0).
    - Testing set: Next 500 rows (split = 'Test').
    - Labels: Uses the dataset's actual 'Machine failure' column to flag anomalies.
    """
    download_dataset()
    raw_df = pd.read_csv(CACHE_FILE)
    
    # Limit to num_samples if requested
    df_subset = raw_df.head(num_samples).copy()
    
    # Map fields to our MQTT DT Schema
    air_temp = df_subset['Air temperature [K]'].values - 273.15
    rot_speed = df_subset['Rotational speed [rpm]'].values
    torque = df_subset['Torque [Nm]'].values
    
    time_steps = np.arange(len(df_subset))
    
    # Map labels based on actual machine failure flags in the dataset
    failures = df_subset['Machine failure'].values
    labels = np.where(failures == 1, 'Anomalous', 'Normal')
    
    # Set train/test split: first 500 rows are Train, next 500 rows are Test
    split = np.array(['Test'] * len(df_subset), dtype=object)
    
    # Locate normal instances in first 500 rows for training
    normal_indices = np.where(failures == 0)[0]
    train_indices = normal_indices[normal_indices < 500]
    split[train_indices] = 'Train'
    
    df = pd.DataFrame({
        'time': time_steps,
        'rotationalSpeed': rot_speed,
        'airTemperature': air_temp,
        'torque': torque,
        'label': labels,
        'split': split
    })
    
    return df

def plot_dataset(df, save_path="dataset_overview.png"):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    # 1. Air Temperature Subplot
    ax1.plot(df['time'], df['airTemperature'], label='Air Temperature (°C)', color='red', alpha=0.8)
    # Highlight actual machine failures on the temp line
    anomalies = df[df['label'] == 'Anomalous']
    ax1.scatter(anomalies['time'], anomalies['airTemperature'], color='black', marker='x', s=30, zorder=5, label='Actual Machine Failure')
    ax1.axhline(y=120, color='darkred', linestyle='--', alpha=0.7, label='Layer A Hard Bound (120°C)')
    ax1.set_title('Air Temperature telemetry stream & Layer A Hard Bound')
    ax1.set_ylabel('Temperature (°C)')
    ax1.set_ylim(-10, 140)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # 2. Rotational Speed Subplot
    ax2.plot(df['time'], df['rotationalSpeed'], label='Rotational Speed (RPM)', color='blue', alpha=0.8)
    ax2.axhline(y=3000, color='darkblue', linestyle='--', alpha=0.7, label='Layer A Hard Bound (3000 RPM)')
    ax2.set_title('Rotational Speed telemetry stream & Layer A Hard Bound')
    ax2.set_ylabel('Speed (RPM)')
    ax2.set_ylim(-100, 3300)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # 3. Torque Subplot
    ax3.plot(df['time'], df['torque'], label='Torque (Nm)', color='green', alpha=0.8)
    ax3.axhline(y=100, color='darkgreen', linestyle='--', alpha=0.7, label='Layer A Hard Bound (100 Nm)')
    ax3.set_title('Torque telemetry stream & Layer A Hard Bound')
    ax3.set_ylabel('Torque (Nm)')
    ax3.set_xlabel('Time Steps')
    ax3.set_ylim(-10, 115)
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Plot saved to {save_path}")

if __name__ == "__main__":
    import os
    dir_path = os.path.dirname(os.path.abspath(__file__))
    print("Generating telemetry data from UCI dataset...")
    dataset = generate_telemetry_data()
    
    # Save to CSV
    csv_path = os.path.join(dir_path, "telemetry_dataset.csv")
    dataset.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path} ({len(dataset)} records).")
    
    # Generate Plot
    plot_path = os.path.join(dir_path, "dataset_overview.png")
    plot_dataset(dataset, save_path=plot_path)
