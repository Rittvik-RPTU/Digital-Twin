import paho.mqtt.client as mqtt
import time
import json
import os

# Load details from the ACL to ensure we are in sync
try:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    acl_path = os.path.join(base_dir, 'users_acl.json')
    with open(acl_path, 'r') as f:
        ACL = json.load(f)
except Exception as e:
    print(f"Error loading users_acl.json: {e}")
    exit(1)

def run_test_for_user(username, password, allowed_project, unauthorized_project=None):
    print(f"\n" + "="*50)
    print(f" RUNNING SECURITY TEST FOR USER: {username}")
    print("="*50)
    
    results = {"connected": False, "sub_allowed": False, "sub_denied": False, "pub_kicked": False}

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[OK] Authentication successful.")
            results["connected"] = True
        else:
            print(f"[FAIL] Connection failed with code {rc}")

    def on_subscribe(client, userdata, mid, reason_codes, properties=None):
        for rc in reason_codes:
            if rc.value == 0:
                print(f"[OK] Subscription to project granted.")
                results["sub_allowed"] = True
            elif rc.value == 135: # 0x87 Not Authorized
                print(f"[SECURITY] Subscription to unauthorized project REJECTED (Reason 0x87).")
                results["sub_denied"] = True

    def on_disconnect(client, userdata, rc, properties=None):
        if rc == 135:
            print(f"[SECURITY] Broker forcibly disconnected client for unauthorized PUBLISH.")
            results["pub_kicked"] = True

    client = mqtt.Client(client_id=f"test-{username}", protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_disconnect = on_disconnect
    client.username_pw_set(username, password)

    try:
        client.connect("localhost", 1883)
        client.loop_start()
        time.sleep(1)

        if not results["connected"]:
            return results

        # Test 1: Subscribe to allowed project
        print(f" -> Testing access to ALLOWED project: {allowed_project}")
        client.subscribe(f"{allowed_project}/telemetry")
        time.sleep(1)

        # Test 2: Subscribe to unauthorized project (if provided)
        if unauthorized_project:
            print(f" -> Testing access to UNAUTHORIZED project: {unauthorized_project}")
            client.subscribe(f"{unauthorized_project}/telemetry")
            time.sleep(1)

            # Test 3: Publish to unauthorized project (should kick)
            print(f" -> Testing PUBLISH to UNAUTHORIZED project (should trigger kick)...")
            client.publish(f"{unauthorized_project}/telemetry", "Malicious Data")
            time.sleep(1)

        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"Error during test: {e}")
    
    return results

if __name__ == "__main__":
    # Test User 1: testuser (Hardcoded in mock server, allowed 990e...)
    # Password is 'testpass' for testuser
    run_test_for_user("testuser", "testpass", "990e8400-e29b-41d4-a716-999999999999", "550e8400-e29b-41d4-a716-446655440000")

    # Test User 2: student1 (Dynamic in mock server, allowed abcd...)
    # Password is 'pass' for dynamic users
    run_test_for_user("student1", "pass", "abcd1234-e29b-41d4-a716-446655449999", "550e8400-e29b-41d4-a716-446655440000")

    # Test User 3: admin (Allowed 550e...)
    run_test_for_user("admin", "admin", "550e8400-e29b-41d4-a716-446655440000")

    # Test 4: Physical Twin (API Key Authentication & Device Isolation)
    print(f"\n" + "="*50)
    print(f" RUNNING SECURITY TEST FOR: PHYSICAL TWIN")
    print("="*50)
    
    pt_client = mqtt.Client(client_id="sensor-01", protocol=mqtt.MQTTv5)
    # Username is always PHYSICAL_TWIN, password is the API Key
    pt_client.username_pw_set("PHYSICAL_TWIN", "pt-secret-key-01")
    
    pt_connected = False
    def on_pt_connect(client, userdata, flags, rc, properties=None):
        global pt_connected
        if rc == 0:
            print("[OK] PT Authentication via API Key successful.")
            pt_connected = True
        else:
            print(f"[FAIL] PT Connection failed with code {rc}")
            
    def on_pt_disconnect(client, userdata, rc, properties=None):
        if rc == 135:
            print("[SECURITY] PT disconnected for publishing outside its device namespace.")
            
    pt_client.on_connect = on_pt_connect
    pt_client.on_disconnect = on_pt_disconnect
    
    try:
        pt_client.connect("localhost", 1883)
        pt_client.loop_start()
        time.sleep(1)
        
        if pt_connected:
            proj = "990e8400-e29b-41d4-a716-999999999999"
            dev = "sensor-01"
            
            print(f" -> Testing PUBLISH to allowed device topic: {proj}/{dev}/status")
            pt_client.publish(f"{proj}/{dev}/status", "ON")
            time.sleep(1)
            
            print(f" -> Testing PUBLISH to unauthorized device topic in same project: {proj}/sensor-02/status")
            pt_client.publish(f"{proj}/sensor-02/status", "HACK")
            time.sleep(1)
            
        pt_client.loop_stop()
        pt_client.disconnect()
    except Exception as e:
        print(f"Error during PT test: {e}")
