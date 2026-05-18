import paho.mqtt.client as mqtt
import json
import os
import pandas as pd
import time
from z_score_monitor import ZScoreMonitor
from if_monitor import IsolationForestMonitor
from fuzzy_engine import FuzzyTrustEngine

# --- Configuration ---
BROKER_HOST = "localhost"
TOPIC = "990e8400-e29b-41d4-a716-999999999999/sensor-01/telemetry"
MQTT_USER = os.environ.get("DT_USERNAME", "testuser")
MQTT_PASS = os.environ.get("DT_PASSWORD", "testpass")

# --- Initialize FAAD Pipeline ---
print("[Layer B] Initializing Live FAAD Pipeline...")
z_monitor = ZScoreMonitor(window_size=30)
if_monitor = IsolationForestMonitor(contamination=0.02)
fuzzy_engine = FuzzyTrustEngine()

# Pre-train the IF Monitor on the baseline data
csv_path = "telemetry_dataset.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    baseline_data = df.iloc[0:150][['speed', 'temperature']].values.tolist()
    if_monitor.train(baseline_data)
else:
    print(f"Warning: {csv_path} not found. IF Monitor will not be trained.")

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[Layer B] Connected to DigitalTwinServer (Broker). Subscribing to: {TOPIC}")
        client.subscribe(TOPIC)
    else:
        print(f"[Layer B] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        temp = float(payload.get("temperature", 0))
        speed = float(payload.get("speed", 0))
        
        # Process through Layer B pipeline
        z = z_monitor.process(temp)
        i_f = if_monitor.score(speed, temp)
        trust = fuzzy_engine.evaluate(z, i_f)
        
        # Determine status for printing
        status = "🟢 OK"
        if trust < 0.3:
            status = "🔴 CRITICAL (Anomaly Detected!)"
        elif trust < 0.7:
            status = "🟡 WARNING (Suspicious)"
            
        print(f"[Layer B] RX: temp={temp:5.1f} | speed={speed:5.1f} || Z-Score: {z:4.1f} | IF: {i_f:4.2f} || Trust: {trust:4.2f} -> {status}")
        
    except Exception as e:
        print(f"[Layer B] Error processing message: {e}")

# --- Setup MQTT Client ---
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, protocol=mqtt.MQTTv5)
except AttributeError:
    client = mqtt.Client(protocol=mqtt.MQTTv5)

client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_connect = on_connect
client.on_message = on_message

print("[Layer B] Starting Live Monitor... Waiting for data from Layer A (Broker)...")
print("-" * 80)
try:
    client.connect(BROKER_HOST, 1883)
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[Layer B] Shutting down monitor.")
    client.disconnect()
