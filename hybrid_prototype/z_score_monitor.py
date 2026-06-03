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
    z_trq_monitor = ZScoreMonitor(window_size=30)
    
    # Process stream
    z_max_scores = []
    for _, row in df.iterrows():
        z_t = z_temp_monitor.process(row['airTemperature'])
        z_s = z_spd_monitor.process(row['rotationalSpeed'])
        z_q = z_trq_monitor.process(row['torque'])
        z_max_scores.append(max(z_t, z_s, z_q))
        
    df['z_max_score'] = z_max_scores
    
    # Plot results
    fig, ax = plt.subplots(figsize=(14, 5))
    
    # Z-Score Plot
    ax.plot(df['time'], df['z_max_score'], label='Z_max Score', color='blue')
    ax.axhline(y=3.0, color='orange', linestyle='--', label='Typical Hard Threshold (Z=3)')
    
    # Highlight actual machine failure time steps
    failures = df[df['label'] == 'Anomalous']
    ax.scatter(failures['time'], [3.0] * len(failures), color='red', marker='x', s=100, zorder=5, label='Actual Machine Failure')
    
    ax.set_title("Maximum Z-Score Monitor Output ($Z_{max}$)")
    ax.set_xlabel("Time Steps")
    ax.set_ylabel("Z-Score")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = os.path.join(dir_path, "z_score_test.png")
    plt.savefig(save_path, dpi=300)
    print(f"Test complete. Plot saved to {save_path}")
