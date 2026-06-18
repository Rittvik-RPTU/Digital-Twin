import paho.mqtt.client as mqtt
import subprocess
import time
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

processes = []

try:
    print("[Test] Starting mock server...")
    mock_server_proc = subprocess.Popen(
        ["python3", "tests/mock_agila_server.py"],
        cwd=base_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(mock_server_proc)
    time.sleep(1.0)

    print("[Test] Starting C++ Broker...")
    broker_proc = subprocess.Popen(
        ["./build/Release/out/DigitalTwinServer"],
        cwd=base_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(broker_proc)
    time.sleep(2.0)

    print("[Test] Connecting as Physical Twin with plaintext API Key...")
    client = mqtt.Client(client_id="pt-test", protocol=mqtt.MQTTv5)
    connected = [False]
    
    def on_connect(c, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[Client] ✓ Physical Twin connected successfully via API Key!")
            connected[0] = True
        else:
            print(f"[Client] ✗ Connection failed with rc={rc}")

    client.on_connect = on_connect
    # Pass the plaintext key, the server should hash it and find it!
    client.username_pw_set("PHYSICAL_TWIN", "sk-pt-a1b2c3d4")
    
    client.connect("localhost", 1883)
    client.loop_start()
    
    time.sleep(2)
    
    if connected[0]:
        print("\n[SUCCESS] The C++ Broker successfully hashed the incoming plaintext key and validated it!")
    else:
        print("\n[FAIL] Physical Twin authentication failed.")
        
    client.loop_stop()
    client.disconnect()
    
finally:
    for p in processes:
        p.terminate()
