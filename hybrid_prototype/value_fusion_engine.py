import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# Import previous monitors
from z_score_monitor import ZScoreMonitor
from if_monitor import IsolationForestMonitor

class ValueFusionTrustEngine:
    """
    Data-Validation Layer B (Component 3): Decision Fusion
    Uses value fusion inference to combine the statistical Z-Score and structural IF-Score 
    into a single continuous 'Trust Index'.
    """
    def __init__(self):
        pass

    def evaluate(self, z_val, if_val):
        """
        Computes the final Trust Index given the two anomaly scores.
        """
        z_val = float(np.clip(z_val, 0.0, 10.0))
        if_val = float(np.clip(if_val, 0.0, 1.0))

        # 1. Membership Mapping for Z-Score
        # Normal membership (0 to 2, peaking <= 1)
        if z_val <= 1.0:
            z_normal = 1.0
        elif 1.0 < z_val < 2.0:
            z_normal = 2.0 - z_val
        else:
            z_normal = 0.0

        # Suspect membership (triangular 1 to 3, peaking at 2)
        if z_val <= 1.0 or z_val >= 3.0:
            z_suspect = 0.0
        elif 1.0 < z_val < 2.0:
            z_suspect = z_val - 1.0
        else:
            z_suspect = 3.0 - z_val

        # Anomalous membership (>= 2, reaching 1 at >= 3)
        if z_val <= 2.0:
            z_anomalous = 0.0
        elif 2.0 < z_val < 3.0:
            z_anomalous = z_val - 2.0
        else:
            z_anomalous = 1.0

        # 2. Membership Mapping for Isolation Forest Score (0=normal, 1=anomalous, transition 0.4 to 0.6)
        if if_val <= 0.4:
            if_normal = 1.0
            if_anomalous = 0.0
        elif 0.4 < if_val < 0.6:
            if_normal = (0.6 - if_val) / 0.2
            if_anomalous = (if_val - 0.4) / 0.2
        else:
            if_normal = 0.0
            if_anomalous = 1.0

        # 3. Rule Evaluation & Centroid Aggregation
        # Rule 1: Both anomalous -> Low trust (0.1)
        # Rule 2: Suspect Z + IF anomaly -> Low trust (0.1)
        # Rule 3: Anomalous Z + IF normal -> Low-Medium trust (0.3)
        # Rule 4: Normal Z + IF anomaly -> Medium trust (0.5)
        # Rule 5: Suspect Z + IF normal -> Medium trust (0.5)
        # Rule 6: Both normal -> High trust (0.9)
        rules = [
            (min(z_anomalous, if_anomalous), 0.1),
            (min(z_suspect, if_anomalous), 0.1),
            (min(z_anomalous, if_normal), 0.3),
            (min(z_normal, if_anomalous), 0.5),
            (min(z_suspect, if_normal), 0.5),
            (min(z_normal, if_normal), 0.9),
        ]

        numerator = sum(w * c for w, c in rules)
        denominator = sum(w for w, _ in rules)

        if denominator == 0:
            return 0.9

        return float(numerator / denominator)

if __name__ == "__main__":
    print("Testing VFAAD Pipeline (Z-Score + Isolation Forest -> Value Fusion Engine)...")
    
    # 1. Load/Generate Data Dynamically (Randomized on each run)
    try:
        from data_generator import generate_telemetry_data
        df = generate_telemetry_data(randomize=False)
        dir_path = os.path.dirname(os.path.abspath(__file__))
        df.to_csv(os.path.join(dir_path, "telemetry_dataset.csv"), index=False)
    except Exception as e:
        print(f"Warning: Could not generate data dynamically ({e}). Loading fallback CSV.")
        dir_path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(dir_path, "telemetry_dataset.csv"))
    
    # 2. Initialize Pipeline
    z_temp_monitor = ZScoreMonitor(window_size=30)
    z_spd_monitor = ZScoreMonitor(window_size=30)
    z_chg_monitor = ZScoreMonitor(window_size=30)
    if_monitor = IsolationForestMonitor(contamination=0.02)
    fusion_engine = ValueFusionTrustEngine()
    
    # Pre-train IF Monitor
    train_df = df[df['split'] == 'Train']
    baseline_data = train_df[['temperature', 'speed', 'chargeLevel']].values.tolist()
    if_monitor.train(baseline_data)
    
    # 3. Process Stream
    z_scores = []
    if_scores = []
    trust_indices = []
    
    for _, row in df.iterrows():
        z_temp = z_temp_monitor.process(row['temperature'])
        z_spd = z_spd_monitor.process(row['speed'])
        z_chg = z_chg_monitor.process(row['chargeLevel'])
        z_max = max(z_temp, z_spd, z_chg)
        
        i_f = if_monitor.score(row['temperature'], row['speed'], row['chargeLevel'])
        trust = fusion_engine.evaluate(z_max, i_f)
        
        z_scores.append(z_max)
        if_scores.append(i_f)
        trust_indices.append(trust)
        
    df['z_score'] = z_scores
    df['if_score'] = if_scores
    df['trust_index'] = trust_indices
    
    # 4. Plot Full Pipeline Results
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    # Phase shading & split line on all subplots
    for ax in [ax1, ax2, ax3]:
        # Shade phases: Driving (dodgerblue) vs Fast-Charging (orange)
        ax.axvspan(0, 250, color='dodgerblue', alpha=0.05, label='Driving Phase' if ax == ax1 else "")
        ax.axvspan(250, 500, color='darkorange', alpha=0.05, label='Fast-Charging Phase' if ax == ax1 else "")
        ax.axvspan(500, 750, color='dodgerblue', alpha=0.05)
        ax.axvspan(750, 1000, color='darkorange', alpha=0.05)
        
        # Train/Test boundary line
        ax.axvline(x=500, color='purple', linestyle='-.', linewidth=2.0, label='Train/Test Split Boundary' if ax == ax1 else "")
        
    # Text headers on ax1
    ax1.text(250, ax1.get_ylim()[1] * 0.85, 'TRAINING BASELINE', color='purple', weight='bold', fontsize=10, ha='center')
    ax1.text(750, ax1.get_ylim()[1] * 0.85, 'TEST EVALUATION', color='purple', weight='bold', fontsize=10, ha='center')
    
    # Z-Score
    ax1.plot(df['time'], df['z_score'], label='Z-Score', color='black', linewidth=1.2)
    ax1.axhline(y=3.0, color='red', linestyle='--', label='High Z Threshold (Z=3)')
    ax1.set_title("1. Statistical Anomaly Monitor (Z-Score)")
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # IF-Score
    ax2.plot(df['time'], df['if_score'], label='IF-Score', color='green', linewidth=1.2)
    ax2.axhline(y=0.6, color='black', linestyle='--', label='Anomalous IF Threshold (0.6)')
    ax2.set_title("2. Structural Anomaly Monitor (Isolation Forest)")
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    # Value Fusion Trust Index
    ax3.plot(df['time'], df['trust_index'], label='Trust Index', color='purple', linewidth=2)
    ax3.axhline(y=0.3, color='red', linestyle='--', label='CRITICAL Block Threshold (0.3)')
    ax3.axhline(y=0.7, color='orange', linestyle='--', label='WARNING Threshold (0.7)')
    ax3.fill_between(df['time'], 0, 0.3, color='red', alpha=0.1)
    ax3.fill_between(df['time'], 0.3, 0.7, color='orange', alpha=0.1)
    ax3.fill_between(df['time'], 0.7, 1.0, color='green', alpha=0.1)
    ax3.set_title("3. Value Fusion Trust Engine Output (Decision Fusion)")
    ax3.set_xlabel("Time Steps")
    ax3.set_ylabel("Trust Level (0 to 1)")
    ax3.set_ylim(0, 1.05)
    
    # Annotate Trust Index drops for each anomaly
    # Anomaly 1: t = 520 to 545. Trust drops to ~0.5 (Warning)
    trust_a1_min_idx = df.loc[520:545, 'trust_index'].idxmin()
    trust_a1_min_val = df.loc[trust_a1_min_idx, 'trust_index']
    ax3.annotate('Anomaly 1: SoC Flat\nTrust Index drops (Warning)', 
                 xy=(trust_a1_min_idx, trust_a1_min_val), xytext=(trust_a1_min_idx + 120, trust_a1_min_val + 0.15),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
                 
    # Anomaly 2: t = 800 to 830. Trust drops to <0.3 (Critical Block)
    trust_a2_min_idx = df.loc[800:830, 'trust_index'].idxmin()
    trust_a2_min_val = df.loc[trust_a2_min_idx, 'trust_index']
    ax3.annotate('Anomaly 2: Temp Spike\nTrust Index drops (Critical)', 
                 xy=(trust_a2_min_idx, trust_a2_min_val), xytext=(trust_a2_min_idx - 100, trust_a2_min_val + 0.1),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
                 
    # Anomaly 3: t = 850 to 860. Trust drops to <0.3 (Critical Block)
    trust_a3_min_idx = df.loc[850:860, 'trust_index'].idxmin()
    trust_a3_min_val = df.loc[trust_a3_min_idx, 'trust_index']
    ax3.annotate('Anomaly 3: Speed Spike\nTrust Index drops (Critical)', 
                 xy=(trust_a3_min_idx, trust_a3_min_val), xytext=(trust_a3_min_idx - 100, trust_a3_min_val - 0.1),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
                 
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path_vfaad = os.path.join(dir_path, "vfaad_pipeline_test.png")
    plt.savefig(save_path_vfaad, dpi=300)
    save_path_faad = os.path.join(dir_path, "faad_pipeline_test.png")
    plt.savefig(save_path_faad, dpi=300)
    print(f"VFAAD Pipeline test complete. Master Plot saved to {save_path_vfaad} (and {save_path_faad})")

