import subprocess
import time
import json
import os
import sys
import socket
import paho.mqtt.client as mqtt

# Base directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def is_port_in_use(port):
    """Check if a port is already open on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def create_mqtt_client(client_id):
    """Create a client compatible with both paho-mqtt v1 and v2."""
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id, protocol=mqtt.MQTTv5)
    except AttributeError:
        return mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)

def main():
    print("="*80)
    print(" STARTING DUAL-LAYER SECURITY INTEGRATION TEST ENVIRONMENT")
    print("="*80)

    processes = []
    results = {
        "case1_layer_a_rejected": False,
        "case2_layer_b_rejected": False,
        "case3_both_accepted": False
    }

    try:
        # 1. Mock Agila Server (port 8088)
        if is_port_in_use(8088):
            print("[Orchestrator] Port 8088 is already in use. Reusing existing Mock Agila Server.")
        else:
            mock_server_cmd = ["python3", "tests/mock_agila_server.py"]
            print(f"[Orchestrator] Starting Mock Agila Server: {' '.join(mock_server_cmd)}")
            mock_server_proc = subprocess.Popen(
                mock_server_cmd,
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append(("Mock Agila", mock_server_proc))
            time.sleep(1.0)

        # 2. FAAD Microservice (port 8089)
        if is_port_in_use(8089):
            print("[Orchestrator] Port 8089 is already in use. Reusing existing FAAD Service.")
        else:
            faad_cmd = ["python3", "hybrid_prototype/faad_service.py"]
            print(f"[Orchestrator] Starting FAAD Microservice: {' '.join(faad_cmd)}")
            faad_proc = subprocess.Popen(
                faad_cmd,
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append(("FAAD Service", faad_proc))
            time.sleep(1.0)

        # 3. C++ DigitalTwinServer Broker (port 1883)
        broker_started_by_us = False
        if is_port_in_use(1883):
            print("[Orchestrator] Port 1883 is already in use. Reusing existing C++ Broker.")
        else:
            broker_cmd = ["./build/Release/out/DigitalTwinServer"]
            print(f"[Orchestrator] Starting DigitalTwinServer: {' '.join(broker_cmd)}")
            broker_proc = subprocess.Popen(
                broker_cmd,
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append(("C++ Broker", broker_proc))
            broker_started_by_us = True

        # Allow newly started processes to bind and initialize
        print("[Orchestrator] Checking and waiting for all services...")
        time.sleep(2.0)

        # Check if any process we started crashed
        for name, proc in processes:
            if proc.poll() is not None:
                print(f"[Orchestrator][FAIL] {name} terminated early with code {proc.poll()}")
                out, err = proc.communicate()
                print(f"[{name} STDOUT]\n{out}\n[{name} STDERR]\n{err}")
                raise RuntimeError(f"Required service {name} failed to start.")

        print("[Orchestrator] System validation environment ready. Initiating test cases...")
        project_id = "990e8400-e29b-41d4-a716-999999999999"
        device_id = "device123"
        topic = f"{project_id}/{device_id}/telemetry"

        # =====================================================================
        # CASE 1: Hard Bounds (Layer A) Violation
        # Temp = 130.0°C (Max allowed in SysML model: 120.0°C)
        # =====================================================================
        print("\n" + "-"*60)
        print("[CASE 1] Out-of-Bounds Check (Temp = 130.0°C)")
        print("-"*60)
        client1 = create_mqtt_client("client-case1-bounds-fail")
        client1.username_pw_set("admin", "admin")

        def on_disconnect_c1(client, userdata, rc, properties=None):
            print(f"[Client 1] Disconnected from broker (rc={rc})")
            if rc != 0:
                results["case1_layer_a_rejected"] = True
                print("[Client 1][SUCCESS] Connection closed as expected due to Layer A rejection.")

        client1.on_disconnect = on_disconnect_c1
        client1.connect("localhost", 1883)
        client1.loop_start()
        time.sleep(0.5)

        payload_c1 = {"temperature": 130.0, "speed": 100.0, "chargeLevel": 75.0}
        print(f"[Client 1] Publishing: {payload_c1}")
        client1.publish(topic, json.dumps(payload_c1))
        time.sleep(2.0)
        client1.loop_stop()
        client1.disconnect()

        # =====================================================================
        # CASE 2: Statistical Anomaly (Layer B / FAAD) Violation
        # Temp = 80.0°C (In-bounds for Layer A, but anomalous for FAAD)
        # =====================================================================
        print("\n" + "-"*60)
        print("[CASE 2] Statistical Anomaly Check (Temp = 80.0°C)")
        print("-"*60)
        client2 = create_mqtt_client("client-case2-faad-fail")
        client2.username_pw_set("admin", "admin")

        def on_disconnect_c2(client, userdata, rc, properties=None):
            print(f"[Client 2] Disconnected from broker (rc={rc})")
            if rc != 0:
                results["case2_layer_b_rejected"] = True
                print("[Client 2][SUCCESS] Connection closed as expected due to FAAD anomaly rejection.")

        client2.on_disconnect = on_disconnect_c2
        client2.connect("localhost", 1883)
        client2.loop_start()
        time.sleep(0.5)

        payload_c2 = {"temperature": 80.0, "speed": 100.0, "chargeLevel": 75.0}
        print(f"[Client 2] Publishing: {payload_c2}")
        client2.publish(topic, json.dumps(payload_c2))
        time.sleep(2.0)
        client2.loop_stop()
        client2.disconnect()

        # =====================================================================
        # CASE 3: Valid Telemetry (Both Layers Pass)
        # Temp = 52.0°C (Normal operating conditions)
        # =====================================================================
        print("\n" + "-"*60)
        print("[CASE 3] Valid Telemetry Check (Temp = 52.0°C)")
        print("-"*60)
        client3 = create_mqtt_client("client-case3-success")
        client3.username_pw_set("admin", "admin")
        
        c3_disconnected = False

        def on_disconnect_c3(client, userdata, rc, properties=None):
            nonlocal c3_disconnected
            print(f"[Client 3] Disconnected from broker (rc={rc})")
            c3_disconnected = True

        client3.on_disconnect = on_disconnect_c3
        client3.connect("localhost", 1883)
        client3.loop_start()
        time.sleep(0.5)

        payload_c3 = {"temperature": 52.0, "speed": 100.0, "chargeLevel": 75.0}
        print(f"[Client 3] Publishing: {payload_c3}")
        client3.publish(topic, json.dumps(payload_c3))
        time.sleep(2.0)

        if not c3_disconnected:
            results["case3_both_accepted"] = True
            print("[Client 3][SUCCESS] Connection remained active. Payload accepted and routed.")

        client3.loop_stop()
        client3.disconnect()

    except Exception as e:
        print(f"[Orchestrator][ERROR] Exception during execution: {e}")

    finally:
        print("\n" + "="*80)
        print(" TEARDOWN AND SERVICE LOGS")
        print("="*80)
        
        # Shutdown services that were started by us
        for name, proc in processes:
            print(f"\nShutting down {name} (PID: {proc.pid})...")
            try:
                proc.terminate()
                out, err = proc.communicate(timeout=2)
                lines = out.strip().split("\n")
                last_lines = "\n".join(lines[-20:]) if len(lines) > 20 else out
                print(f"--- {name} STDOUT (Recent) ---\n{last_lines}")
                if err:
                    print(f"--- {name} STDERR ---\n{err}")
            except Exception as teardown_ex:
                print(f"Error terminating {name}: {teardown_ex}")
                try:
                    proc.kill()
                except:
                    pass

        # Final Summary
        print("\n" + "="*80)
        print(" FINAL DUAL-LAYER SECURITY TEST RESULTS:")
        print(f" Case 1 (Layer A Violation Rejected):  {results['case1_layer_a_rejected']}")
        print(f" Case 2 (Layer B/FAAD Anomaly Rejected): {results['case2_layer_b_rejected']}")
        print(f" Case 3 (Normal Telemetry Accepted):    {results['case3_both_accepted']}")
        print("="*80)

        if all(results.values()):
            print(">>> ALL INTEGRATION TEST CASES PASSED SUCCESSFULLY! <<<")
            sys.exit(0)
        else:
            print(">>> INTEGRATION TEST FAILURES DETECTED! <<<")
            sys.exit(1)

if __name__ == "__main__":
    main()
