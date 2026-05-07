#!/usr/bin/env python3

import time
import sys
import threading
import paho.mqtt.client as mqtt

def print_header(text):
    print(f"\n{'='*50}\n{text}\n{'='*50}")

def main():
    print_header("Digital Twin Integrity & Security Test Suite")
    print("Please ensure the DigitalTwinServer and mock_agila_server are running before executing this script.")
    time.sleep(2)

    # Attack 1: Attempt to Spoof the Heartbeat
    print_header("Attack 1: Spoofing the Integrity Heartbeat")
    print("Attempting to publish to dt/system/integrity as a normal user")
    
    def on_publish_spoof(client, userdata, mid, reason_code, properties):
        if reason_code.is_failure:
            print(f"[SUCCESS] Command failed as expected (Reason code: {reason_code})")
        else:
            print("[ERROR] Command succeeded unexpectedly! Server didn't block it.")
        client.disconnect()

    client1 = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
    client1.username_pw_set("testuser", "testpass")
    client1.on_publish = on_publish_spoof
    client1.connect("localhost", 1883)
    client1.publish("dt/system/integrity", '{"status":"fake_ok"}')
    client1.loop_forever()

    # Attack 2: Attempt to cause a Denial of Service (DoS) by spamming large payloads
    print_header("Attack 2: Resource Exhaustion / Large Packet")
    print("Generating a 50KB payload to stress the broker...")
    large_payload = "A" * 50000 
    
    def on_publish_dos(client, userdata, mid, reason_code, properties):
        if not reason_code.is_failure:
            print("[SUCCESS] Broker handled the payload gracefully.")
        else:
            print(f"[WARNING] Broker rejected the large payload: {reason_code}")
        client.disconnect()

    client2 = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
    client2.username_pw_set("testuser", "testpass")
    client2.on_publish = on_publish_dos
    client2.connect("localhost", 1883)
    client2.publish("dt/test", large_payload)
    client2.loop_forever()

    # Verification: Check if Heartbeat is still alive
    print_header("Verification: Is the Heartbeat Still Alive?")
    print("We will subscribe to the heartbeat topic. We expect to receive at least one heartbeat (sent every 10s).")
    
    heartbeat_received = False
    
    def on_message(client, userdata, msg):
        nonlocal heartbeat_received
        heartbeat_received = True
        print("[SUCCESS] Received heartbeat payload:")
        print(f"  {msg.payload.decode()}")
        client.disconnect()
        
    client3 = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
    client3.username_pw_set("testuser", "testpass")
    client3.on_message = on_message
    client3.connect("localhost", 1883)
    client3.subscribe("dt/system/integrity")
    
    start_time = time.time()
    while time.time() - start_time < 12 and not heartbeat_received:
        client3.loop(0.1)

    if heartbeat_received:
        print("Conclusion: The server survived the attacks and the heartbeat is functioning normally.")
    else:
        print("[ERROR] Failed to receive heartbeat within 12 seconds. The server might be compromised or frozen!")

if __name__ == "__main__":
    main()

