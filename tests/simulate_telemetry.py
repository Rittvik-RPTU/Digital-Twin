"""
Telemetry Simulator
===================
Phase 1 — Baseline: normal car operation (~50°C, ~80 km/h)
Phase 2 — Hard-bounds attack: temperature 150°C → blocked by Layer A (DISCONNECT)
"""

import paho.mqtt.client as mqtt
import json
import time
import random

BROKER_HOST = "localhost"
TOPIC = "990e8400-e29b-41d4-a716-999999999999/sensor-01/telemetry"

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, protocol=mqtt.MQTTv5)
except AttributeError:
    client = mqtt.Client(protocol=mqtt.MQTTv5)

import os

MQTT_USER = os.environ.get("DT_USERNAME", "testuser")
MQTT_PASS = os.environ.get("DT_PASSWORD", "testpass")

client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(BROKER_HOST, 1883)

def publish(temp, speed, label=""):
    payload = {"temperature": temp, "speed": speed}
    client.publish(TOPIC, json.dumps(payload))
    print(f"  [{label}] temp={temp:.1f}°C  speed={speed:.1f} km/h")
    time.sleep(0.1)

import csv

csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "hybrid_prototype", "telemetry_dataset.csv")

print(f"\n── Starting Telemetry Simulation from Research Dataset ──")
print(f"Reading from: {csv_path}\n")

try:
    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        
        # Adding a small hard-bounds attack at the end manually just to prove Layer A works
        rows = list(reader)
        rows.append({"time": "999", "speed": "80.0", "temperature": "150.0", "label": "LAYER-A HARD ATTACK"})
        
        for row in rows:
            temp = float(row['temperature'])
            speed = float(row['speed'])
            label = row['label']
            
            publish(temp, speed, label=label)
            
            # If the broker disconnects us (e.g. Layer A kills connection), paho-mqtt might throw or we might just need to reconnect.
            # But for this simple script, we just let it run. If it fails, the user will see it in the broker logs.

except FileNotFoundError:
    print(f"Error: Could not find the dataset at {csv_path}")

time.sleep(1)
client.disconnect()
print("\nSimulation complete.")
