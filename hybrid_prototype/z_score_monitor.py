import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import deque

class ZScoreMonitor:
    """
    Data-Validation Layer B (Component 1): Statistical Anomaly Detector
    Calculates the Z-Score of an incoming feature stream using a rolling window.
    """
    def __init__(self, window_size=50):
        self.window_size = window_size
        self.window = deque(maxlen=window_size)
    
    def process(self, value):
        """
        Ingests a new value, updates the rolling window, and returns the Z-score.
        """
        # Append to window
        self.window.append(value)
        
        # Warm-up phase
        if len(self.window) < self.window_size:
            return 0.0
        
        # Calculate local statistics
        window_array = np.array(self.window)
        mean = np.mean(window_array)
        std = np.std(window_array)
        
        # Prevent division by zero if all values in window are identical
        if std == 0:
            std = 1e-6
            
        z_score = (value - mean) / std
        return abs(z_score)

if __name__ == "__main__":
    print("Testing Z-Score Monitor on synthetic dataset...")
    
    # Load dataset
    import os
    dir_path = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(dir_path, "telemetry_dataset.csv"))
    
    # Initialize monitors for all three attributes
    z_temp_monitor = ZScoreMonitor(window_size=30)
    z_spd_monitor = ZScoreMonitor(window_size=30)
    z_chg_monitor = ZScoreMonitor(window_size=30)
    
    # Process stream
    z_max_scores = []
    for _, row in df.iterrows():
        z_t = z_temp_monitor.process(row['temperature'])
        z_s = z_spd_monitor.process(row['speed'])
        z_c = z_chg_monitor.process(row['chargeLevel'])
        z_max_scores.append(max(z_t, z_s, z_c))
        
    df['z_max_score'] = z_max_scores
    
    # Plot results
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Shade phases: Driving (dodgerblue) vs Fast-Charging (orange)
    ax.axvspan(0, 250, color='dodgerblue', alpha=0.06, label='Driving Phase')
    ax.axvspan(250, 500, color='darkorange', alpha=0.06, label='Fast-Charging Phase')
    ax.axvspan(500, 750, color='dodgerblue', alpha=0.06)
    ax.axvspan(750, 1000, color='darkorange', alpha=0.06)
    
    # Train/Test boundary line
    ax.axvline(x=500, color='purple', linestyle='-.', linewidth=2.0, label='Train/Test Split Boundary')
    
    # Z-Score Plot
    ax.plot(df['time'], df['z_max_score'], label='Max Z-Score ($Z_{max}$)', color='blue', linewidth=1.5)
    ax.axhline(y=3.0, color='red', linestyle='--', label='Statistical Threshold (Z=3)')
    
    # Highlight actual EV anomaly time steps
    failures = df[df['label'] == 'Anomalous']
    ax.scatter(failures['time'], [3.0] * len(failures), color='black', marker='x', s=60, zorder=5, label='Injected EV Anomaly')
    
    # Text headers for train and test splits
    ax.text(250, ax.get_ylim()[1] * 0.9, 'TRAINING BASELINE', color='purple', weight='bold', fontsize=10, ha='center')
    ax.text(750, ax.get_ylim()[1] * 0.9, 'TEST EVALUATION', color='purple', weight='bold', fontsize=10, ha='center')
    
    # Annotate key spikes in Test Split
    # Find max Z-score times for Anomaly 2 and 3
    # Anomaly 2: t in [800, 830]
    # Anomaly 3: t in [850, 860]
    z_a2_max_idx = df.loc[800:830, 'z_max_score'].idxmax()
    z_a2_max_val = df.loc[z_a2_max_idx, 'z_max_score']
    ax.annotate(f'Temp Anomaly Spike\n(Z = {z_a2_max_val:.2f})', xy=(z_a2_max_idx, z_a2_max_val), xytext=(z_a2_max_idx - 120, z_a2_max_val - 2.0),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
                 
    z_a3_max_idx = df.loc[850:860, 'z_max_score'].idxmax()
    z_a3_max_val = df.loc[z_a3_max_idx, 'z_max_score']
    ax.annotate(f'Speed Bound Spike\n(Z = {z_a3_max_val:.2f})', xy=(z_a3_max_idx, z_a3_max_val), xytext=(z_a3_max_idx - 100, z_a3_max_val + 1.0),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
    
    ax.set_title("Layer B: Statistical Anomaly Monitor Output ($Z_{max}$)")
    ax.set_xlabel("Time Steps")
    ax.set_ylabel("Z-Score Magnitude")
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = os.path.join(dir_path, "z_score_test.png")
    plt.savefig(save_path, dpi=300)
    print(f"Test complete. Plot saved to {save_path}")
