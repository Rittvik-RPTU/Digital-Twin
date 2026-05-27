import json
import pickle
import numpy as np
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import os

# Load the trained FAAD model
dir_path = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(dir_path, "faad_model.pkl")
try:
    with open(model_path, "rb") as f:
        model_data = pickle.load(f)
        clf = model_data["isolation_forest"]
        means = model_data["means"]
        stds = model_data["stds"]
        print(f"[FAAD Service] Successfully loaded model data from {model_path}")
except Exception as e:
    print(f"[FAAD Service] Error loading model: {e}")
    exit(1)

def evaluate_fuzzy_logic(z_max, if_score):
    # 1. Fuzzification for Z-Score
    # Normal Z-Score membership
    if z_max <= 1.0:
        z_normal = 1.0
    elif 1.0 < z_max < 2.0:
        z_normal = 2.0 - z_max
    else:
        z_normal = 0.0
        
    # Suspect Z-Score membership
    if z_max <= 1.0 or z_max >= 3.0:
        z_suspect = 0.0
    elif 1.0 < z_max < 2.0:
        z_suspect = z_max - 1.0
    else: # 2.0 <= z_max < 3.0
        z_suspect = 3.0 - z_max
        
    # Anomalous Z-Score membership
    if z_max <= 2.0:
        z_anomalous = 0.0
    elif 2.0 < z_max < 3.0:
        z_anomalous = z_max - 2.0
    else:
        z_anomalous = 1.0

    # 2. Fuzzification for Isolation Forest score (normal is >= 0, anomaly is negative)
    # Normal membership
    if if_score >= 0.0:
        if_normal = 1.0
    elif -0.1 < if_score < 0.0:
        if_normal = (if_score + 0.1) / 0.1
    else:
        if_normal = 0.0
        
    # Anomalous membership
    if if_score <= -0.1:
        if_anomalous = 1.0
    elif -0.1 < if_score < 0.0:
        if_anomalous = -if_score / 0.1
    else:
        if_anomalous = 0.0

    # 3. Rule Evaluation & Defuzzification (Weighted Average Method)
    # Output Centroids: Low = 0.1, Medium = 0.5, High = 0.9
    rules = [
        (min(z_anomalous, if_anomalous), 0.1), # Rule 1: Both anomalous -> Low trust
        (min(z_suspect, if_anomalous), 0.1),   # Rule 2: Suspect + IF anomaly -> Low trust
        (min(z_normal, if_anomalous), 0.5),    # Rule 3: Normal Z + IF anomaly -> Medium trust
        (min(z_suspect, if_normal), 0.5),      # Rule 4: Suspect Z + IF normal -> Medium trust
        (min(z_normal, if_normal), 0.9),       # Rule 5: Both normal -> High trust
        (min(z_anomalous, if_normal), 0.3),    # Rule 6: Anomalous Z + IF normal -> Low-Medium trust
    ]
    
    numerator = sum(w * c for w, c in rules)
    denominator = sum(w for w, _ in rules)
    
    if denominator == 0:
        return 0.9 # Default to High trust if no rules fire (should not happen)
    
    return numerator / denominator

class FAADRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        if self.path == "/evaluate":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode() if content_length > 0 else ''
            
            try:
                data = json.loads(body)
                payload = data.get("payload", {})
                
                # Extract telemetry fields and fill missing with historical averages
                temp = float(payload.get("temperature", means["temperature"]))
                spd = float(payload.get("speed", means["speed"]))
                chg = float(payload.get("chargeLevel", means["chargeLevel"]))
                
                # 1. Z-Score Calculation
                z_temp = abs(temp - means["temperature"]) / stds["temperature"]
                z_spd = abs(spd - means["speed"]) / stds["speed"]
                z_chg = abs(chg - means["chargeLevel"]) / stds["chargeLevel"]
                z_max = max(z_temp, z_spd, z_chg)
                
                # 2. Isolation Forest Evaluation
                sample = np.array([[temp, spd, chg]])
                if_score = float(clf.decision_function(sample)[0])
                
                # 3. Fuzzy Logic Fusion
                trust_index = evaluate_fuzzy_logic(z_max, if_score)
                
                response_data = {
                    "trust_index": trust_index,
                    "z_score_max": z_max,
                    "isolation_forest_score": if_score
                }
                
                print(f"[FAAD Service] Evaluated payload: Temp={temp:.1f}, Spd={spd:.1f}, Chg={chg:.1f} "
                      f"-> Z_max={z_max:.2f}, IF_score={if_score:.3f} -> Trust={trust_index:.3f}")
                      
                self._send_json(200, response_data)
                
            except Exception as e:
                print(f"[FAAD Service] Error processing request: {e}")
                self._send_json(400, {"error": str(e)})
        else:
            self._send_json(404, {"error": "Not Found"})

def run(port=8089):
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, FAADRequestHandler)
    print(f"[FAAD Service] Starting fuzzy anomaly detection service on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
