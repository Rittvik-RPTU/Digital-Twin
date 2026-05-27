import paho.mqtt.client as mqtt
import time
import json
import os
import sys

def main():
    print("="*60)
    print(" STARTING FAAD (LAYER B) PIPELINE INTEGRATION TEST")
    print("="*60)
    
    project_id = "990e8400-e29b-41d4-a716-999999999999"
    device_id = "device123"
    topic = f"{project_id}/{device_id}/telemetry"

    # Test results tracking
    results = {"normal_accepted": True, "anomalous_rejected": False}

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[OK] Connected to broker")
        else:
            print(f"[FAIL] Connection failed: {rc}")

    def on_disconnect(client, userdata, rc, properties=None):
        print(f"[INFO] Disconnected from broker with code: {rc}")
        if rc == 0x9c or rc == 135 or rc == 156: # payload_format_invalid/not_authorized
            results["anomalous_rejected"] = True

    # 1. Normal Client Test
    print("\n[Test 1] Publishing normal telemetry sequence...")
    client = mqtt.Client(client_id="normal-pt", protocol=mqtt.MQTTv5)
    client.username_pw_set("admin", "admin")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect("localhost", 1883)
        client.loop_start()
        time.sleep(0.5)

        # Publish normal payload
        normal_payload = {
            "temperature": 50.0,
            "speed": 100.0,
            "chargeLevel": 75.0
        }
        print(f"Publishing normal payload: {normal_payload}")
        client.publish(topic, json.dumps(normal_payload))
        time.sleep(1.5)

        # Verify client is still connected by checking if disconnected was called
        if results["anomalous_rejected"]:
            print("[FAIL] Broker disconnected client on normal payload!")
            results["normal_accepted"] = False
        else:
            print("[OK] Normal payload accepted. Client remains connected.")

        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"[ERROR] Normal test failed: {e}")
        results["normal_accepted"] = False

    # 2. Anomalous Client Test
    print("\n[Test 2] Publishing anomalous (in-bounds but statistically suspect) telemetry...")
    client2 = mqtt.Client(client_id="anomalous-pt", protocol=mqtt.MQTTv5)
    client2.username_pw_set("admin", "admin")
    client2.on_connect = on_connect
    
    def on_anomalous_disconnect(client, userdata, rc, properties=None):
        print(f"[INFO] Anomalous client disconnected with code: {rc}")
        if rc != 0:
            results["anomalous_rejected"] = True

    client2.on_disconnect = on_anomalous_disconnect

    try:
        client2.connect("localhost", 1883)
        client2.loop_start()
        time.sleep(0.5)

        # Publish anomalous payload
        # Note: Temperature 80C is within Layer A bounds [0, 120] but is > 6 std devs from mean 50C
        anomalous_payload = {
            "temperature": 80.0,
            "speed": 100.0,
            "chargeLevel": 75.0
        }
        print(f"Publishing anomalous payload: {anomalous_payload}")
        client2.publish(topic, json.dumps(anomalous_payload))
        
        # Wait to let broker evaluate and disconnect
        time.sleep(2.0)

        if results["anomalous_rejected"]:
            print("[OK] Server successfully detected statistical anomaly and disconnected client.")
        else:
            print("[FAIL] Server did NOT disconnect client for anomalous payload!")

        client2.loop_stop()
        client2.disconnect()
    except Exception as e:
        print(f"[ERROR] Anomalous test failed: {e}")

    print("\n" + "="*50)
    print(" FAAD PIPELINE TEST SUMMARY:")
    print(f" Normal Accepted:     {results['normal_accepted']}")
    print(f" Anomalous Rejected:  {results['anomalous_rejected']}")
    print("="*50)

    if results['normal_accepted'] and results['anomalous_rejected']:
        print(">>> ALL TESTS PASSED SUCCESSFULLY! <<<")
        sys.exit(0)
    else:
        print(">>> SOME TESTS FAILED! <<<")
        sys.exit(1)

if __name__ == "__main__":
    main()
