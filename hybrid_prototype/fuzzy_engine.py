import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Import previous monitors
from z_score_monitor import ZScoreMonitor
from if_monitor import IsolationForestMonitor

class FuzzyTrustEngine:
    """
    Data-Validation Layer B (Component 3): Decision Fusion
    Uses fuzzy logic to combine the statistical Z-Score and structural IF-Score 
    into a single continuous 'Trust Index'.
    """
    def __init__(self):
        # 1. Define Fuzzy Variables
        # Antecedents (Inputs)
        self.z_score = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'z_score')
        self.if_score = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'if_score')
        
        # Consequent (Output)
        self.trust_index = ctrl.Consequent(np.arange(0, 1.01, 0.01), 'trust_index')

        # 2. Define Membership Functions
        # Z-Score sets: Normal (0-2), Suspect (1-3), Anomalous (>2)
        self.z_score['normal'] = fuzz.zmf(self.z_score.universe, 1.0, 2.0)
        self.z_score['suspect'] = fuzz.trimf(self.z_score.universe, [1.0, 2.0, 3.0])
        self.z_score['anomalous'] = fuzz.smf(self.z_score.universe, 2.0, 3.0)

        # IF-Score sets: Normal (low anomaly score), Anomalous (high anomaly score)
        self.if_score['normal'] = fuzz.zmf(self.if_score.universe, 0.4, 0.6)
        self.if_score['anomalous'] = fuzz.smf(self.if_score.universe, 0.4, 0.6)

        # Trust Index sets: Low (centroid 0.1), Low-Medium (centroid 0.3), Medium (centroid 0.5), High (centroid 0.9)
        self.trust_index['low'] = fuzz.trimf(self.trust_index.universe, [0.0, 0.1, 0.25])
        self.trust_index['low_medium'] = fuzz.trimf(self.trust_index.universe, [0.15, 0.3, 0.45])
        self.trust_index['medium'] = fuzz.trimf(self.trust_index.universe, [0.35, 0.5, 0.65])
        self.trust_index['high'] = fuzz.trimf(self.trust_index.universe, [0.75, 0.9, 1.0])

        # 3. Define Fuzzy Rules
        rule1 = ctrl.Rule(self.z_score['anomalous'] & self.if_score['anomalous'], self.trust_index['low'])
        rule2 = ctrl.Rule(self.z_score['suspect'] & self.if_score['anomalous'], self.trust_index['low'])
        rule3 = ctrl.Rule(self.z_score['anomalous'] & self.if_score['normal'], self.trust_index['low_medium'])
        rule4 = ctrl.Rule(self.z_score['normal'] & self.if_score['anomalous'], self.trust_index['medium'])
        rule5 = ctrl.Rule(self.z_score['suspect'] & self.if_score['normal'], self.trust_index['medium'])
        rule6 = ctrl.Rule(self.z_score['normal'] & self.if_score['normal'], self.trust_index['high'])

        # 4. Build Control System
        self.trust_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6])
        self.trust_sim = ctrl.ControlSystemSimulation(self.trust_ctrl)

    def evaluate(self, z_val, if_val):
        """
        Computes the final Trust Index given the two anomaly scores.
        """
        # Clip inputs to universe bounds to prevent out-of-range errors
        self.trust_sim.input['z_score'] = np.clip(z_val, 0, 10.0)
        self.trust_sim.input['if_score'] = np.clip(if_val, 0, 1.0)
        
        self.trust_sim.compute()
        return self.trust_sim.output['trust_index']

if __name__ == "__main__":
    print("Testing FAAD Pipeline (Z-Score + Isolation Forest -> Fuzzy Engine)...")
    
    # 1. Load/Generate Data Dynamically (Randomized on each run)
    try:
        from data_generator import generate_telemetry_data
        df = generate_telemetry_data(randomize=False)
        import os
        dir_path = os.path.dirname(os.path.abspath(__file__))
        df.to_csv(os.path.join(dir_path, "telemetry_dataset.csv"), index=False)
    except Exception as e:
        print(f"Warning: Could not generate data dynamically ({e}). Loading fallback CSV.")
        import os
        dir_path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(dir_path, "telemetry_dataset.csv"))
    
    # 2. Initialize Pipeline
    z_temp_monitor = ZScoreMonitor(window_size=30)
    z_spd_monitor = ZScoreMonitor(window_size=30)
    z_chg_monitor = ZScoreMonitor(window_size=30)
    if_monitor = IsolationForestMonitor(contamination=0.02)
    fuzzy_engine = FuzzyTrustEngine()
    
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
        trust = fuzzy_engine.evaluate(z_max, i_f)
        
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
    
    # Fuzzy Trust Index
    ax3.plot(df['time'], df['trust_index'], label='Trust Index', color='purple', linewidth=2)
    ax3.axhline(y=0.3, color='red', linestyle='--', label='CRITICAL Block Threshold (0.3)')
    ax3.axhline(y=0.7, color='orange', linestyle='--', label='WARNING Threshold (0.7)')
    ax3.fill_between(df['time'], 0, 0.3, color='red', alpha=0.1)
    ax3.fill_between(df['time'], 0.3, 0.7, color='orange', alpha=0.1)
    ax3.fill_between(df['time'], 0.7, 1.0, color='green', alpha=0.1)
    ax3.set_title("3. Fuzzy Trust Engine Output (Decision Fusion)")
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
    save_path = os.path.join(dir_path, "faad_pipeline_test.png")
    plt.savefig(save_path, dpi=300)
    print(f"FAAD Pipeline test complete. Master Plot saved to {save_path}")
