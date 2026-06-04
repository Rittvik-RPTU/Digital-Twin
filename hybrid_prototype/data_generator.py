import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_telemetry_data(num_samples=1000, randomize=False):
    """
    Simulates high-fidelity EV telemetry data modeled after the Stanford Real-world EV dataset.
    Features: speed (km/h), temperature (°C), chargeLevel (%)
    Splits:
    - Train (Time 0 to 500): Normal driving baseline (Machine failure == 0/Normal).
    - Test (Time 500 to 1000): Standard operations, containing statistical and contextual anomalies.
    """
    np.random.seed(42)
    time_steps = np.arange(num_samples)
    
    speed = np.zeros(num_samples)
    temperature = np.zeros(num_samples)
    charge_level = np.zeros(num_samples)
    labels = np.array(['Normal'] * num_samples, dtype=object)
    
    # Baseline normal behavior simulation
    curr_temp = 22.0
    curr_charge = 95.0
    ambient_temp = 22.0
    
    for t in range(num_samples):
        # 1. Normal State Logic (Driving vs Charging in a 500-step cycle)
        cycle_step = t % 500
        if cycle_step < 250: # Driving Phase
            # Speed oscillates smoothly (representing urban/highway driving)
            target_spd = 55.0 + 35.0 * np.sin(t / 25.0) + np.random.normal(0, 2.0)
            spd = max(0.0, target_spd)
            
            # SoC decays depending on speed
            discharge_rate = (spd * 0.0015 + 0.03)
            curr_charge = max(0.0, curr_charge - discharge_rate)
            
            # Temperature increases with speed (current) and cools down to ambient
            heat_gen = (spd * 0.07)
            heat_diss = 0.08 * (curr_temp - ambient_temp)
            curr_temp += 0.05 * (heat_gen - heat_diss) + np.random.normal(0, 0.1)
        else: # Fast-Charging Phase (speed = 0)
            spd = 0.0
            
            # SoC increases linearly/tapering
            charge_rate = 0.25 if curr_charge < 80.0 else 0.1
            curr_charge = min(100.0, curr_charge + charge_rate)
            
            # Temp rises during fast charging and cools down
            heat_gen = 2.5 if curr_charge < 80.0 else 0.8
            heat_diss = 0.06 * (curr_temp - ambient_temp)
            curr_temp += 0.05 * (heat_gen - heat_diss) + np.random.normal(0, 0.1)
            
        speed[t] = spd
        temperature[t] = curr_temp
        charge_level[t] = curr_charge

    # 2. Inject Anomalies into Test Split (t >= 500) to ensure Train split remains completely clean
    
    # Anomaly 1: Contextual/Multivariate Anomaly (Flat SoC while driving) at t = 520 to 545
    # Speed is high (~85 km/h) but charge level remains flat (no depletion)
    for t in range(520, 545):
        speed[t] = 85.0 + np.random.normal(0, 1.0)
        charge_level[t] = charge_level[520] # Hold charge level constant
        temperature[t] = temperature[520] + np.random.normal(0, 0.2)
        labels[t] = 'Anomalous'
        
    # Anomaly 2: Z-Score temperature spike at t = 800 to 830 (during fast-charge)
    # Temperature spikes up to 56°C (above normal charging temperature of ~38°C)
    for t in range(800, 830):
        temperature[t] = 56.0 + np.random.normal(0, 0.5)
        labels[t] = 'Anomalous'
        
    # Anomaly 3: Layer A Hard Bound violation at t = 850 to 860
    # Speed spikes to 265 km/h (exceeding 250 km/h hard bound)
    for t in range(850, 860):
        speed[t] = 265.0
        labels[t] = 'Anomalous'

    # Set train/test split: first 500 rows are Train, next 500 are Test
    split = np.array(['Test'] * num_samples, dtype=object)
    
    # Locate normal instances in first 500 rows for training
    normal_indices = np.where(labels == 'Normal')[0]
    train_indices = normal_indices[normal_indices < 500]
    split[train_indices] = 'Train'
    
    df = pd.DataFrame({
        'time': time_steps,
        'speed': speed,
        'temperature': temperature,
        'chargeLevel': charge_level,
        'label': labels,
        'split': split
    })
    
    return df

def plot_dataset(df, save_path="dataset_overview.png"):
    # Slice to show only one clean cycle (first 500 steps)
    plot_df = df[df['time'] < 500]
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    
    # Visual phase distinction shading
    for ax in [ax1, ax2, ax3]:
        # Shade phases: Driving (dodgerblue) vs Fast-Charging (orange)
        ax.axvspan(0, 250, color='dodgerblue', alpha=0.07, label='Driving Phase' if ax == ax1 else "")
        ax.axvspan(250, 500, color='darkorange', alpha=0.07, label='Fast-Charging Phase' if ax == ax1 else "")
        
    # 1. Temperature Subplot
    ax1.plot(plot_df['time'], plot_df['temperature'], label='Battery Temperature (°C)', color='red', alpha=0.8)
    ax1.axhline(y=120, color='darkred', linestyle='--', alpha=0.7, label='Layer A Hard Bound (120°C)')
    ax1.set_title('Raw Telemetry: Battery Temperature')
    ax1.set_ylabel('Temperature (°C)')
    ax1.set_ylim(-10, 140)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # 2. Speed Subplot
    ax2.plot(plot_df['time'], plot_df['speed'], label='Vehicle Speed (km/h)', color='blue', alpha=0.8)
    ax2.axhline(y=250, color='darkblue', linestyle='--', alpha=0.7, label='Layer A Hard Bound (250 km/h)')
    ax2.set_title('Raw Telemetry: Vehicle Speed')
    ax2.set_ylabel('Speed (km/h)')
    ax2.set_ylim(-10, 280)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # 3. State of Charge Subplot
    ax3.plot(plot_df['time'], plot_df['chargeLevel'], label='State of Charge (%)', color='green', alpha=0.8)
    ax3.axhline(y=100, color='darkgreen', linestyle='--', alpha=0.7, label='Layer A Hard Bound (100%)')
    ax3.set_title('Raw Telemetry: State of Charge (SoC)')
    ax3.set_ylabel('State of Charge (%)')
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
    print("Generating telemetry data from Stanford EV-inspired model...")
    dataset = generate_telemetry_data()
    
    # Save to CSV
    csv_path = os.path.join(dir_path, "telemetry_dataset.csv")
    dataset.to_csv(csv_path, index=False)
    print(f"Dataset saved to {csv_path} ({len(dataset)} records).")
    
    # Generate Plot
    plot_path = os.path.join(dir_path, "dataset_overview.png")
    plot_dataset(dataset, save_path=plot_path)
