import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

class IsolationForestMonitor:
    """
    Data-Validation Layer B (Component 2): Structural Anomaly Detector
    Uses multivariate Isolation Forest to detect anomalies in [temperature, speed, chargeLevel] correlation.
    """
    def __init__(self, contamination=0.05):
        self.clf = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False

    def train(self, data_points):
        """
        Trains the model on a baseline of normal data.
        data_points: List of [temperature, speed, chargeLevel] vectors.
        """
        X = np.array(data_points)
        self.clf.fit(X)
        self.is_trained = True
        print(f"[IF Monitor] Model trained on {len(data_points)} samples.")

    def score(self, temp, speed, charge_level):
        """
        Returns an anomaly score between 0 and 1.
        1.0 = Highly Anomalous, 0.0 = Normal.
        """
        if not self.is_trained:
            return 0.0
        
        X_live = np.array([[temp, speed, charge_level]])
        
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
    
    # Phase 1: Training on the first 500 samples (Normal baseline)
    train_df = df[df['split'] == 'Train']
    baseline_data = train_df[['temperature', 'speed', 'chargeLevel']].values.tolist()
    if_monitor.train(baseline_data)
    
    # Phase 2: Scoring the full stream
    if_scores = []
    for _, row in df.iterrows():
        s = if_monitor.score(row['temperature'], row['speed'], row['chargeLevel'])
        if_scores.append(s)
        
    df['if_score'] = if_scores
    
    # Plot results
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Shade phases: Driving (dodgerblue) vs Fast-Charging (orange)
    ax.axvspan(0, 250, color='dodgerblue', alpha=0.06, label='Driving Phase')
    ax.axvspan(250, 500, color='darkorange', alpha=0.06, label='Fast-Charging Phase')
    ax.axvspan(500, 750, color='dodgerblue', alpha=0.06)
    ax.axvspan(750, 1000, color='darkorange', alpha=0.06)
    
    # Train/Test boundary line
    ax.axvline(x=500, color='purple', linestyle='-.', linewidth=2.0, label='Train/Test Split Boundary')
    
    # IF Score Plot
    ax.plot(df['time'], df['if_score'], label='IF Anomaly Score', color='green', linewidth=1.5)
    ax.axhline(y=0.6, color='black', linestyle='--', label='Detection Threshold (0.6)')
    
    # Highlight actual EV anomaly time steps
    failures = df[df['label'] == 'Anomalous']
    ax.scatter(failures['time'], [0.6] * len(failures), color='purple', marker='o', s=30, zorder=5, label='Injected EV Anomaly')
    
    # Text headers for train and test splits
    ax.text(250, ax.get_ylim()[1] * 0.9, 'TRAINING BASELINE', color='purple', weight='bold', fontsize=10, ha='center')
    ax.text(750, ax.get_ylim()[1] * 0.9, 'TEST EVALUATION', color='purple', weight='bold', fontsize=10, ha='center')
    
    # Annotate key anomaly regions in Test Split
    # Anomaly 1: Flat SoC during Driving (t = 520 to 545)
    if_a1_max_idx = df.loc[520:545, 'if_score'].idxmax()
    if_a1_max_val = df.loc[if_a1_max_idx, 'if_score']
    ax.annotate('Anomaly 1: Flat SoC\n(Multivariate Correlation)', xy=(if_a1_max_idx, if_a1_max_val), xytext=(if_a1_max_idx + 120, if_a1_max_val + 0.05),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
                 
    # Anomaly 2: Temp Spike during Charging (t = 800 to 830)
    if_a2_max_idx = df.loc[800:830, 'if_score'].idxmax()
    if_a2_max_val = df.loc[if_a2_max_idx, 'if_score']
    ax.annotate('Anomaly 2: Temp Spike\n(Structural Anomaly)', xy=(if_a2_max_idx, if_a2_max_val), xytext=(if_a2_max_idx - 100, if_a2_max_val + 0.05),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
                 
    # Anomaly 3: Speed Spike (t = 850 to 860)
    if_a3_max_idx = df.loc[850:860, 'if_score'].idxmax()
    if_a3_max_val = df.loc[if_a3_max_idx, 'if_score']
    ax.annotate('Anomaly 3: Speed Bound\n(Point Anomaly)', xy=(if_a3_max_idx, if_a3_max_val), xytext=(if_a3_max_idx - 100, if_a3_max_val - 0.05),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
    
    ax.set_title("Layer B: Structural Anomaly Monitor Output (Isolation Forest)")
    ax.set_xlabel("Time Steps")
    ax.set_ylabel("Anomaly Score (0=Normal, 1=Anomalous)")
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = os.path.join(dir_path, "if_test.png")
    plt.savefig(save_path, dpi=300)
    print(f"Test complete. Plot saved to {save_path}")
