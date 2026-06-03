import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

class IsolationForestMonitor:
    """
    Data-Validation Layer B (Component 2): Structural Anomaly Detector
    Uses multivariate Isolation Forest to detect anomalies in [airTemperature, rotationalSpeed, torque] correlation.
    """
    def __init__(self, contamination=0.05):
        self.clf = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False

    def train(self, data_points):
        """
        Trains the model on a baseline of normal data.
        data_points: List of [airTemperature, rotationalSpeed, torque] vectors.
        """
        X = np.array(data_points)
        self.clf.fit(X)
        self.is_trained = True
        print(f"[IF Monitor] Model trained on {len(data_points)} samples.")

    def score(self, air_temp, rot_speed, torque):
        """
        Returns an anomaly score between 0 and 1.
        1.0 = Highly Anomalous, 0.0 = Normal.
        """
        if not self.is_trained:
            return 0.0
        
        X_live = np.array([[air_temp, rot_speed, torque]])
        
        # scikit-learn's score_samples returns the opposite of the anomaly score 
        # defined in the original Liu et al. (2008) paper.
        # Negating it gives us the standard paper score, natively bounded [0, 1]
        # where values closer to 1.0 indicate strong anomalies.
        paper_anomaly_score = -self.clf.score_samples(X_live)[0]
        
        return float(paper_anomaly_score)

if __name__ == "__main__":
    print("Testing Isolation Forest Monitor on synthetic dataset...")
    
    # Load dataset
    import os
    dir_path = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(dir_path, "telemetry_dataset.csv"))
    
    # Initialize monitor
    if_monitor = IsolationForestMonitor(contamination=0.02)
    
    # Phase 1: Training on the first 5000 samples (Normal baseline)
    train_df = df[df['split'] == 'Train']
    baseline_data = train_df[['airTemperature', 'rotationalSpeed', 'torque']].values.tolist()
    if_monitor.train(baseline_data)
    
    # Phase 2: Scoring the full stream
    if_scores = []
    for _, row in df.iterrows():
        s = if_monitor.score(row['airTemperature'], row['rotationalSpeed'], row['torque'])
        if_scores.append(s)
        
    df['if_score'] = if_scores
    
    # Plot results
    fig, ax = plt.subplots(figsize=(14, 5))
    
    # IF Score Plot
    ax.plot(df['time'], df['if_score'], label='IF Anomaly Score', color='green')
    ax.axhline(y=0.6, color='black', linestyle='--', label='Detection Threshold')
    
    # Highlight actual machine failure time steps
    failures = df[df['label'] == 'Anomalous']
    ax.scatter(failures['time'], [0.6] * len(failures), color='purple', marker='o', s=30, zorder=5, label='Actual Machine Failure')
    
    ax.set_title("Isolation Forest Monitor Output")
    ax.set_xlabel("Time Steps")
    ax.set_ylabel("Anomaly Score (0=Normal, 1=Anomalous)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = os.path.join(dir_path, "if_test.png")
    plt.savefig(save_path, dpi=300)
    print(f"Test complete. Plot saved to {save_path}")
