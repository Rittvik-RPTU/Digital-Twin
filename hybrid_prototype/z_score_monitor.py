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
    df = pd.read_csv("telemetry_dataset.csv")
    
    # Initialize monitor
    z_monitor = ZScoreMonitor(window_size=30)
    
    # Process stream
    z_scores = []
    for temp in df['temperature']:
        z = z_monitor.process(temp)
        z_scores.append(z)
        
    df['z_score_temp'] = z_scores
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # Top plot: Raw Data
    ax1.plot(df['time'], df['temperature'], label='Temperature (°C)', color='red', alpha=0.8)
    stat_anom = df[df['label'] == 'Statistical Anomaly']
    ax1.scatter(stat_anom['time'], stat_anom['temperature'], color='black', marker='x', s=100, label='Statistical Spike')
    ax1.set_title("Raw Temperature Stream")
    ax1.set_ylabel("Temperature")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Bottom plot: Z-Score
    ax2.plot(df['time'], df['z_score_temp'], label='Z-Score (Magnitude)', color='blue')
    ax2.axhline(y=3.0, color='orange', linestyle='--', label='Typical Hard Threshold (Z=3)')
    ax2.set_title("Z-Score Monitor Output")
    ax2.set_xlabel("Time Steps")
    ax2.set_ylabel("Z-Score")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = "z_score_test.png"
    plt.savefig(save_path, dpi=300)
    print(f"Test complete. Plot saved to {save_path}")
