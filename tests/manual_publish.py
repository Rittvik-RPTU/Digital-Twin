import paho.mqtt.client as mqtt
import json
import argparse
import sys

def create_mqtt_client(client_id):
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id, protocol=mqtt.MQTTv5)
    except AttributeError:
        return mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)

def main():
    parser = argparse.ArgumentParser(description="Publish custom telemetry to the C++ Broker.")
    parser.add_argument("--temp", type=float, required=True, help="Temperature value in °C")
    parser.add_argument("--speed", type=float, default=100.0, help="Speed value in km/h (default: 100.0)")
    parser.add_argument("--charge", type=float, default=75.0, help="Charge level in %% (default: 75.0)")
    
    args = parser.parse_args()

    project_id = "990e8400-e29b-41d4-a716-999999999999"
    device_id = "device123"
    topic = f"{project_id}/{device_id}/telemetry"

    client = create_mqtt_client("manual-test-publisher")
    client.username_pw_set("admin", "admin")

    def on_disconnect(client, userdata, rc, properties=None):
        if rc != 0:
            print(f"\n[Client] ✗ Disconnected by Broker! Reason/Return Code: {rc}")
            print("[Client] This indicates the payload was REJECTED by either Layer A (bounds) or Layer B (FAAD).")
        else:
            print("\n[Client] Gracefully disconnected.")

    client.on_disconnect = on_disconnect

    try:
        print(f"[Client] Connecting to C++ Broker on localhost:1883...")
        client.connect("localhost", 1883)
        client.loop_start()
        
        # Wait up to 3 seconds for connection to establish
        connected = False
        for _ in range(30):
            if client.is_connected():
                connected = True
                break
            time.sleep(0.1)
            
        if not connected:
            print("\n[Client] ✗ Failed to connect to broker (Connection Timeout).")
            client.loop_stop()
            return

        payload = {
            "temperature": args.temp,
            "speed": args.speed,
            "chargeLevel": args.charge
        }
        
        print(f"[Client] Publishing payload: {payload}")
        print(f"[Client] Topic: {topic}")
        
        info = client.publish(topic, json.dumps(payload))
        info.wait_for_publish(timeout=2.0)
        
        # Give the broker time to process and potentially disconnect us
        time_to_wait = 1.5
        sys.stdout.write("[Client] Waiting to check connection state...")
        sys.stdout.flush()
        
        disconnected = False
        for _ in range(int(time_to_wait * 10)):
            if not client.is_connected():
                disconnected = True
                break
            time.sleep(0.1)
            
        if not disconnected:
            print("\n[Client] ✓ Connection active. Payload was ACCEPTED by all security layers.")
            
        client.loop_stop()
        client.disconnect()
        
    except Exception as e:
        print(f"[Client] Error connecting/publishing: {e}")

if __name__ == "__main__":
    import time
    main()
