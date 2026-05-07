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

client.username_pw_set("testuser", "testpass")
client.connect(BROKER_HOST, 1883)

def publish(temp, speed, label=""):
    payload = {"temperature": temp, "speed": speed}
    client.publish(TOPIC, json.dumps(payload))
    print(f"  [{label}] temp={temp:.1f}°C  speed={speed:.1f} km/h")
    time.sleep(0.1)

print("\n── Phase 1: Baseline (50 normal messages) ──────────────────")
for i in range(50):
    temp  = 50.0 + random.uniform(-1.0, 1.0)   # 49–51°C
    speed = 80.0 + random.uniform(-2.0, 2.0)   # 78–82 km/h
    publish(temp, speed, label="NORMAL")

print("\n── Phase 2: Layer A Test — Hard-bounds violation ────────────")
print("  Sending temperature=150°C  (expect DISCONNECT from broker)")
publish(150.0, 80.0, label="LAYER-A ATTACK")
time.sleep(1)

client.disconnect()
print("\nSimulation complete.")
