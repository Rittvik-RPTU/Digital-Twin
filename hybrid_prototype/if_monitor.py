import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

class IsolationForestMonitor:
    """
    Data-Validation Layer B (Component 2): Structural Anomaly Detector
    Uses multivariate Isolation Forest to detect anomalies in [speed, temperature] correlation.
    """
    def __init__(self, contamination=0.05):
        self.clf = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False
        self.training_data = []

    def train(self, data_points):
        """
        Trains the model on a baseline of normal data.
        data_points: List of [speed, temperature] vectors.
        """
        X = np.array(data_points)
        self.clf.fit(X)
        self.is_trained = True
        print(f"[IF Monitor] Model trained on {len(data_points)} samples.")

    def score(self, speed, temperature):
        """
        Returns an anomaly score between 0 and 1.
        1.0 = Highly Anomalous, 0.0 = Normal.
        """
        if not self.is_trained:
            return 0.0
        
        X_live = np.array([[speed, temperature]])
        
        # scikit-learn's score_samples returns the opposite of the anomaly score 
        # defined in the original Liu et al. (2008) paper.
        # Negating it gives us the standard paper score, natively bounded [0, 1]
        # where values closer to 1.0 indicate strong anomalies.
        paper_anomaly_score = -self.clf.score_samples(X_live)[0]
        
        return float(paper_anomaly_score)

if __name__ == "__main__":
    print("Testing Isolation Forest Monitor on synthetic dataset...")
    
    # Load dataset
    df = pd.read_csv("telemetry_dataset.csv")
    
    # Initialize monitor
    if_monitor = IsolationForestMonitor(contamination=0.02)
    
    # Phase 1: Training on the first 150 samples (Normal baseline)
    baseline_data = df.iloc[0:150][['speed', 'temperature']].values.tolist()
    if_monitor.train(baseline_data)
    
    # Phase 2: Scoring the full stream
    if_scores = []
    for _, row in df.iterrows():
        s = if_monitor.score(row['speed'], row['temperature'])
        if_scores.append(s)
        
    df['if_score'] = if_scores
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # Top plot: Speed & Temperature
    ax1.plot(df['time'], df['speed'], label='Speed (km/h)', color='blue', alpha=0.4)
    ax1.plot(df['time'], df['temperature'], label='Temperature (°C)', color='red', alpha=0.8)
    ctx_anom = df[df['label'] == 'Contextual Anomaly']
    ax1.scatter(ctx_anom['time'], ctx_anom['temperature'], color='purple', marker='o', s=30, label='Contextual Anomaly (IF Target)')
    ax1.set_title("Multi-variate Telemetry Stream")
    ax1.set_ylabel("Value")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Bottom plot: IF Score
    ax2.plot(df['time'], df['if_score'], label='IF Anomaly Score', color='green')
    ax2.axhline(y=0.6, color='black', linestyle='--', label='Detection Threshold')
    ax2.set_title("Isolation Forest Monitor Output")
    ax2.set_xlabel("Time Steps")
    ax2.set_ylabel("Anomaly Score (0=Normal, 1=Anomalous)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = "if_test.png"
    plt.savefig(save_path, dpi=300)
    print(f"Test complete. Plot saved to {save_path}")
