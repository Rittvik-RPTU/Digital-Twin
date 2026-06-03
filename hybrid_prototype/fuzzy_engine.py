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
        # Z-Score sets: Low (0-2), Medium (2-4), High (>4)
        self.z_score['low'] = fuzz.zmf(self.z_score.universe, 1.5, 3.0)
        self.z_score['medium'] = fuzz.gaussmf(self.z_score.universe, 3.0, 0.8)
        self.z_score['high'] = fuzz.smf(self.z_score.universe, 3.0, 5.0)

        # IF-Score sets: Normal (0-0.5), Suspect (0.4-0.7), Anomalous (>0.6)
        self.if_score['normal'] = fuzz.zmf(self.if_score.universe, 0.4, 0.6)
        self.if_score['suspect'] = fuzz.gaussmf(self.if_score.universe, 0.55, 0.1)
        self.if_score['anomalous'] = fuzz.smf(self.if_score.universe, 0.5, 0.7)

        # Trust Index sets: Critical (0-0.3), Warning (0.3-0.7), OK (0.7-1.0)
        self.trust_index['critical'] = fuzz.zmf(self.trust_index.universe, 0.2, 0.4)
        self.trust_index['warning'] = fuzz.gaussmf(self.trust_index.universe, 0.5, 0.15)
        self.trust_index['ok'] = fuzz.smf(self.trust_index.universe, 0.6, 0.8)

        # 3. Define Fuzzy Rules
        rule1 = ctrl.Rule(self.z_score['low'] & self.if_score['normal'], self.trust_index['ok'])
        rule2 = ctrl.Rule(self.z_score['medium'] & self.if_score['normal'], self.trust_index['warning'])
        rule3 = ctrl.Rule(self.z_score['high'] | self.if_score['anomalous'], self.trust_index['critical'])
        rule4 = ctrl.Rule(self.z_score['low'] & self.if_score['suspect'], self.trust_index['warning'])
        rule5 = ctrl.Rule(self.z_score['medium'] & self.if_score['suspect'], self.trust_index['critical'])

        # 4. Build Control System
        self.trust_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5])
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
        df.to_csv("telemetry_dataset.csv", index=False)
    except Exception as e:
        print(f"Warning: Could not generate data dynamically ({e}). Loading fallback CSV.")
        df = pd.read_csv("telemetry_dataset.csv")
    
    # 2. Initialize Pipeline
    z_monitor = ZScoreMonitor(window_size=30)
    if_monitor = IsolationForestMonitor(contamination=0.02)
    fuzzy_engine = FuzzyTrustEngine()
    
    # Pre-train IF Monitor
    baseline_data = df.iloc[0:150][['speed', 'temperature']].values.tolist()
    if_monitor.train(baseline_data)
    
    # 3. Process Stream
    z_scores = []
    if_scores = []
    trust_indices = []
    
    for _, row in df.iterrows():
        z = z_monitor.process(row['temperature'])
        i_f = if_monitor.score(row['speed'], row['temperature'])
        trust = fuzzy_engine.evaluate(z, i_f)
        
        z_scores.append(z)
        if_scores.append(i_f)
        trust_indices.append(trust)
        
    df['z_score'] = z_scores
    df['if_score'] = if_scores
    df['trust_index'] = trust_indices
    
    # 4. Plot Full Pipeline Results
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    
    # Raw Data
    ax1.plot(df['time'], df['speed'], label='Speed (km/h)', color='blue', alpha=0.4)
    ax1.plot(df['time'], df['temperature'], label='Temperature (°C)', color='red', alpha=0.8)
    ax1.set_title("1. Raw Telemetry Stream")
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Z-Score
    ax2.plot(df['time'], df['z_score'], label='Z-Score', color='black')
    ax2.axhline(y=3.0, color='orange', linestyle='--', label='High Z Threshold')
    ax2.set_title("2. Statistical Anomaly Monitor (Z-Score)")
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # IF-Score
    ax3.plot(df['time'], df['if_score'], label='IF-Score', color='green')
    ax3.axhline(y=0.6, color='orange', linestyle='--', label='Anomalous IF Threshold')
    ax3.set_title("3. Structural Anomaly Monitor (Isolation Forest)")
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    # Fuzzy Trust Index
    ax4.plot(df['time'], df['trust_index'], label='Trust Index', color='purple', linewidth=2)
    ax4.axhline(y=0.3, color='red', linestyle='--', label='CRITICAL Block Threshold')
    ax4.axhline(y=0.7, color='orange', linestyle='--', label='WARNING Threshold')
    ax4.fill_between(df['time'], 0, 0.3, color='red', alpha=0.1)
    ax4.fill_between(df['time'], 0.3, 0.7, color='orange', alpha=0.1)
    ax4.fill_between(df['time'], 0.7, 1.0, color='green', alpha=0.1)
    ax4.set_title("4. Fuzzy Trust Engine Output (Decision Fusion)")
    ax4.set_xlabel("Time Steps")
    ax4.set_ylabel("Trust Level (0 to 1)")
    ax4.legend(loc='upper right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path = "faad_pipeline_test.png"
    plt.savefig(save_path, dpi=300)
    print(f"FAAD Pipeline test complete. Master Plot saved to {save_path}")
