import paho.mqtt.client as mqtt
import json
import argparse
import sys

def create_mqtt_client(client_id):
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, protocol=mqtt.MQTTv5)
    except (AttributeError, ValueError):
        return mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)

def main():
    parser = argparse.ArgumentParser(description="Publish custom telemetry to the C++ Broker.")
    parser.add_argument("--temp", type=float, required=True, help="Temperature value")
    parser.add_argument("--speed", type=float, default=100.0, help="Speed value")
    parser.add_argument("--charge", type=float, default=75.0, help="Charge level")
    parser.add_argument("--project", type=str, default="222e8400-e29b-41d4-a716-222222222222", help="Project UUID (default: Vehicle Validation)")
    
    args = parser.parse_args()

    project_id = args.project
    device_id = "device123"
    topic = f"{project_id}/{device_id}/telemetry"

    client = create_mqtt_client("manual-test-publisher")
    client.username_pw_set("admin", "admin")

    def on_disconnect(client, userdata, *args, **kwargs):
        # Support both CallbackAPIVersion.VERSION1 and VERSION2 signatures cleanly
        properties = kwargs.get('properties', None)
        rc = 0
        if len(args) == 1:
            rc = args[0]
        elif len(args) >= 2:
            rc = args[1]
            if len(args) >= 3 and properties is None:
                properties = args[2]

        reason_detail = ""
        if properties and hasattr(properties, "ReasonString") and properties.ReasonString:
            reason_detail = str(properties.ReasonString)
        
        rc_val = getattr(rc, 'value', rc)

        if rc_val != 0 or reason_detail:
            print(f"\n[Client] ✗ Disconnected by Broker!")
            if "Layer A" in reason_detail:
                print(f"[Client] Rejection Reason: REJECTED BY LAYER A (SysML v2 Model Bounds Violation). Details: '{reason_detail}'")
            elif "Layer B" in reason_detail:
                print(f"[Client] Rejection Reason: REJECTED BY LAYER B (FAAD Statistical Anomaly). Details: '{reason_detail}'")
            elif reason_detail:
                print(f"[Client] Rejection Reason: {reason_detail}")
            else:
                print(f"[Client] Rejection Reason: Disconnected with Return Code {rc_val}")
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
