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

def run_bounds_validation_tests():
    """Test Layer A: Model-Derived Bounds Validation."""
    print(f"\n" + "="*50)
    print(f" LAYER A: BOUNDS VALIDATION TESTS")
    print("="*50)

    project_id = "990e8400-e29b-41d4-a716-999999999999"

    # Test 1: Valid temperature payload (within bounds [0, 120])
    print(f"\n[Test 1] Publishing valid temperature payload (50°C)...")
    results = {"valid_accepted": False, "disconnected": False}

    def on_valid_disconnect(client, userdata, rc, properties=None):
        results["disconnected"] = True

    client = mqtt.Client(client_id="bounds-test-valid", protocol=mqtt.MQTTv5)
    client.username_pw_set("testuser", "testpass")
    client.on_disconnect = on_valid_disconnect

    try:
        client.connect("localhost", 1883)
        client.loop_start()
        time.sleep(0.5)

        payload = json.dumps({"temperature": 50.0})
        client.publish(f"{project_id}/telemetry", payload)
        time.sleep(1)

        if not results["disconnected"]:
            print("[OK] Valid payload accepted (not disconnected)")
            results["valid_accepted"] = True
        else:
            print("[FAIL] Server disconnected on valid payload!")

        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"[ERROR] Test 1 failed: {e}")

    # Test 2: Out-of-bounds temperature (violates [0, 120])
    print(f"\n[Test 2] Publishing OOB temperature payload (150°C)...")
    results2 = {"oob_rejected": False}

    def on_oob_disconnect(client, userdata, rc, properties=None):
        if rc == 0x9C:  # payload_format_invalid
            print("[OK] Server disconnected for OOB payload (payload_format_invalid)")
            results2["oob_rejected"] = True
        elif rc in [0x87, 0x83]:  # not_authorized or server_unavailable (fallback)
            print("[OK] Server disconnected for OOB payload")
            results2["oob_rejected"] = True
        else:
            print(f"[WARNING] Disconnected with code {rc:#x}")

    client2 = mqtt.Client(client_id="bounds-test-oob", protocol=mqtt.MQTTv5)
    client2.username_pw_set("testuser", "testpass")
    client2.on_disconnect = on_oob_disconnect

    try:
        client2.connect("localhost", 1883)
        client2.loop_start()
        time.sleep(0.5)

        payload = json.dumps({"temperature": 150.0})  # OOB: > 120
        client2.publish(f"{project_id}/telemetry", payload)
        time.sleep(2)

        if not results2["oob_rejected"]:
            print("[WARNING] Server did NOT disconnect on OOB payload!")

        client2.loop_stop()
        client2.disconnect()
    except Exception as e:
        print(f"[ERROR] Test 2 failed: {e}")

    # Test 3: Out-of-bounds speed (violates [0, 250])
    print(f"\n[Test 3] Publishing OOB speed payload (-10 km/h)...")
    results3 = {"oob_rejected": False}

    def on_speed_disconnect(client, userdata, rc, properties=None):
        if rc == 0x9C or rc in [0x87, 0x83]:
            print("[OK] Server disconnected for OOB speed")
            results3["oob_rejected"] = True

    client3 = mqtt.Client(client_id="bounds-test-speed", protocol=mqtt.MQTTv5)
    client3.username_pw_set("testuser", "testpass")
    client3.on_disconnect = on_speed_disconnect

    try:
        client3.connect("localhost", 1883)
        client3.loop_start()
        time.sleep(0.5)

        payload = json.dumps({"speed": -10.0})  # OOB: < 0
        client3.publish(f"{project_id}/telemetry", payload)
        time.sleep(2)

        if not results3["oob_rejected"]:
            print("[WARNING] Server did NOT disconnect on OOB speed!")

        client3.loop_stop()
        client3.disconnect()
    except Exception as e:
        print(f"[ERROR] Test 3 failed: {e}")

    # Test 4: Mixed payload with multiple attributes
    print(f"\n[Test 4] Publishing mixed payload (temp=50, speed=-10, charge=75)...")
    results4 = {"oob_rejected": False}

    def on_mixed_disconnect(client, userdata, rc, properties=None):
        if rc == 0x9C or rc in [0x87, 0x83]:
            print("[OK] Server disconnected for OOB speed in mixed payload")
            results4["oob_rejected"] = True

    client4 = mqtt.Client(client_id="bounds-test-mixed", protocol=mqtt.MQTTv5)
    client4.username_pw_set("testuser", "testpass")
    client4.on_disconnect = on_mixed_disconnect

    try:
        client4.connect("localhost", 1883)
        client4.loop_start()
        time.sleep(0.5)

        # speed=-10 violates bounds, should cause rejection
        payload = json.dumps({
            "temperature": 50.0,   # Valid [0, 120]
            "speed": -10.0,        # INVALID: < 0
            "chargeLevel": 75.0    # Valid [0, 100]
        })
        client4.publish(f"{project_id}/telemetry", payload)
        time.sleep(2)

        if not results4["oob_rejected"]:
            print("[WARNING] Server did NOT disconnect on mixed OOB payload!")

        client4.loop_stop()
        client4.disconnect()
    except Exception as e:
        print(f"[ERROR] Test 4 failed: {e}")


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

    # Test 5: Bounds Validation (Layer A)
    run_bounds_validation_tests()
