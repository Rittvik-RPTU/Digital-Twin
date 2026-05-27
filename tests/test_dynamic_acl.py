import subprocess
import time
import json
import os
import paho.mqtt.client as mqtt

# 1. Back up users_acl.json
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
acl_path = os.path.join(base_dir, 'users_acl.json')
backup_path = acl_path + '.backup'

with open(acl_path, 'r') as f:
    original_acl_content = f.read()

with open(backup_path, 'w') as f:
    f.write(original_acl_content)

print("[Test] Backed up users_acl.json")

# Helper to restore users_acl.json
def restore_acl():
    print("[Test] Restoring users_acl.json to original state...")
    with open(acl_path, 'w') as f:
        f.write(original_acl_content)
    if os.path.exists(backup_path):
        os.remove(backup_path)

# Helper to clean up processes
def cleanup(processes):
    print("\n--- Process Outputs ---")
    names = ["Mock Server", "Broker"]
    for idx, p in enumerate(processes):
        try:
            p.terminate()
            out, err = p.communicate(timeout=3)
            print(f"[{names[idx]} STDOUT]\n{out}")
            print(f"[{names[idx]} STDERR]\n{err}")
        except Exception as e:
            try:
                p.kill()
                out, err = p.communicate()
                print(f"[{names[idx]} STDOUT (killed)]\n{out}")
                print(f"[{names[idx]} STDERR (killed)]\n{err}")
            except Exception as e2:
                print(f"Error cleaning up {names[idx]}: {e2}")
    restore_acl()

processes = []
try:
    # 2. Start mock Agila server
    mock_server_cmd = ["python3", "tests/mock_agila_server.py"]
    print(f"[Test] Starting mock server: {' '.join(mock_server_cmd)}")
    mock_server_proc = subprocess.Popen(
        mock_server_cmd,
        cwd=base_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(mock_server_proc)

    # Sleep to allow mock server to bind to port
    print("[Test] Waiting for mock server to bind to port...")
    time.sleep(1.5)

    # 3. Start DigitalTwinServer
    broker_cmd = ["./build/Release/out/DigitalTwinServer"]
    print(f"[Test] Starting broker: {' '.join(broker_cmd)}")
    broker_proc = subprocess.Popen(
        broker_cmd,
        cwd=base_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(broker_proc)

    # Wait for broker to initialize
    time.sleep(2.0)

    # Check if they are still running
    if mock_server_proc.poll() is not None:
        print("[FAIL] Mock server failed to start. Output:")
        out, err = mock_server_proc.communicate()
        print(f"STDOUT:\n{out}\nSTDERR:\n{err}")
        cleanup(processes)
        exit(1)

    if broker_proc.poll() is not None:
        print("[FAIL] Broker failed to start. Output:")
        out, err = broker_proc.communicate()
        print(f"STDOUT:\n{out}\nSTDERR:\n{err}")
        cleanup(processes)
        exit(1)

    print("[Test] Mock server and Broker started successfully.")

    # 4. Connect client and try accessing a brand-new project UUID
    # Let's use testuser:testpass
    test_username = "testuser"
    test_password = "testpass"
    new_project_uuid = "88888888-4444-4444-4444-1234567890ab"
    spoofed_project_uuid = "77777777-4444-4444-4444-1234567890ab"

    # Step 4a. Connect client and check if subscribing to new_project_uuid is denied
    results = {"sub_denied": False, "sub_allowed": False, "disconnected": False}

    def on_connect(client, userdata, flags, rc, properties=None):
        print(f"[Client] Connected to broker (rc={rc})")

    def on_subscribe(client, userdata, mid, reason_codes, properties=None):
        for rc in reason_codes:
            print(f"[Client] Subscription response code: {rc.value}")
            if rc.value == 135: # 0x87 Not Authorized
                results["sub_denied"] = True
            elif rc.value == 0:
                results["sub_allowed"] = True

    def on_disconnect(client, userdata, rc, properties=None):
        print(f"[Client] Disconnected from broker (rc={rc})")
        results["disconnected"] = True

    def on_log(client, userdata, level, buf):
        print(f"[Client Log] {buf}")

    client = mqtt.Client(client_id="test-client-dynamic", protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_disconnect = on_disconnect
    client.on_log = on_log
    client.username_pw_set(test_username, test_password)

    client.connect("localhost", 1883)
    client.loop_start()
    time.sleep(1)

    print(f"[Test] Subscribing to unauthorized project topic: {new_project_uuid}/telemetry")
    client.subscribe(f"{new_project_uuid}/telemetry")
    time.sleep(1.5)

    if not results["sub_denied"]:
        print("[FAIL] Subscription to unauthorized project should have been denied but wasn't.")
        cleanup(processes)
        exit(1)
    else:
        print("[OK] Subscription to unauthorized project was correctly denied.")

    # Step 4b. Verify Session Spoofing protection
    # client (authenticated as testuser) tries to register spoofed_project_uuid for 'admin'
    spoof_payload = {
        "username": "admin",
        "projectId": spoofed_project_uuid
    }
    print(f"[Test] Publishing spoofed registration payload (targeting admin) to dt/system/register_project: {spoof_payload}")
    results["disconnected"] = False
    client.publish("dt/system/register_project", json.dumps(spoof_payload))
    time.sleep(2)

    # The broker must disconnect the user for attempting authorization spoofing
    if not results["disconnected"]:
        print("[FAIL] Session spoofing attempt was not blocked (client not disconnected).")
        cleanup(processes)
        exit(1)
    else:
        print("[OK] Session spoofing attempt was BLOCKED. Client was forcibly disconnected.")

    # Verify that the spoofed project was NOT added to admin's projects on disk
    with open(acl_path, 'r') as f:
        updated_acl = json.load(f)
    admin_projects = updated_acl.get("users", {}).get("admin", {}).get("projects", [])
    if spoofed_project_uuid in admin_projects:
        print("[FAIL] Spoofed project was written to admin's ACL file.")
        cleanup(processes)
        exit(1)
    else:
        print("[OK] Spoofed project was NOT written to admin's ACL file.")

    # Stop the disconnected client loop
    client.loop_stop()

    # Step 4c. Reconnect clean client to test valid self-registration
    print("[Test] Reconnecting client for valid self-registration test...")
    results["sub_denied"] = False
    results["sub_allowed"] = False
    results["disconnected"] = False

    client = mqtt.Client(client_id="test-client-dynamic-2", protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_disconnect = on_disconnect
    client.on_log = on_log
    client.username_pw_set(test_username, test_password)

    client.connect("localhost", 1883)
    client.loop_start()
    time.sleep(1)

    reg_payload = {
        "username": test_username,
        "projectId": new_project_uuid
    }
    print(f"[Test] Publishing valid self-registration payload (targeting self) to dt/system/register_project: {reg_payload}")
    msg = client.publish("dt/system/register_project", json.dumps(reg_payload))
    try:
        msg.wait_for_publish(timeout=3)
    except Exception as pe:
        print(f"[FAIL] Publish wait failed: {pe}")
    time.sleep(2) # Give broker time to update config and hot-reload

    # Let's inspect users_acl.json to verify that new_project_uuid was written under testuser's projects
    with open(acl_path, 'r') as f:
        updated_acl = json.load(f)
    
    testuser_projects = updated_acl.get("users", {}).get(test_username, {}).get("projects", [])
    print(f"[Test] Current projects for '{test_username}' in users_acl.json: {testuser_projects}")
    if new_project_uuid not in testuser_projects:
        print(f"[FAIL] {new_project_uuid} was not successfully written to users_acl.json.")
        cleanup(processes)
        exit(1)
    else:
        print(f"[OK] {new_project_uuid} is now present in users_acl.json.")

    # Step 4d. Re-subscribe to the telemetry topic. It should now be ALLOWED!
    print(f"[Test] Subscribing again to project topic: {new_project_uuid}/telemetry")
    client.subscribe(f"{new_project_uuid}/telemetry")
    time.sleep(1.5)

    if results["sub_allowed"]:
        print("[OK] Subscription to newly registered project is now ALLOWED.")
    else:
        print(f"[FAIL] Subscription was not allowed. Reason codes: {results}")
        cleanup(processes)
        exit(1)

    # Let's clean up
    client.loop_stop()
    client.disconnect()
    
    print("\n" + "="*40)
    print(" ALL TESTS (INCLUDING SPOOFING BLOCK) PASSED! ")
    print("="*40)
    cleanup(processes)

except Exception as e:
    print(f"[ERROR] Exception during test execution: {e}")
    cleanup(processes)
    exit(1)
