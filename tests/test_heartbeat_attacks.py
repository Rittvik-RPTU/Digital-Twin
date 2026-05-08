#!/usr/bin/env python3

import time
import sys
import threading
import paho.mqtt.client as mqtt
import os

MQTT_USER = os.environ.get("DT_USERNAME", "testuser")
MQTT_PASS = os.environ.get("DT_PASSWORD", "testpass")

def print_header(text):
    print(f"\n{'='*50}\n{text}\n{'='*50}")

def main():
    print_header("Digital Twin Integrity & Security Test Suite")
    print("Please ensure the DigitalTwinServer and mock_agila_server are running before executing this script.")
    time.sleep(2)

    # Attack 1: Attempt to Spoof the Heartbeat
    print_header("Attack 1: Spoofing the Integrity Heartbeat")
    print("Attempting to publish to dt/system/integrity as a normal user")
    
    spoof_blocked = False

    def on_publish_spoof(client, userdata, mid, reason_code, properties):
        # In QoS 0, on_publish just means the packet was sent. 
        # We wait for the server to disconnect us.
        pass

    def on_disconnect_spoof(client, userdata, disconnect_flags, reason_code, properties):
        nonlocal spoof_blocked
        if reason_code == "not_authorized" or reason_code == 0x87:
            print(f"[SUCCESS] Server disconnected client as expected (Reason: {reason_code})")
            spoof_blocked = True
        else:
            print(f"[WARNING] Disconnected with unexpected code: {reason_code}")

    client1 = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
    client1.username_pw_set(MQTT_USER, MQTT_PASS)
    client1.on_publish = on_publish_spoof
    client1.on_disconnect = on_disconnect_spoof
    client1.connect("localhost", 1883)
    client1.publish("dt/system/integrity", '{"status":"fake_ok"}')
    
    # Wait a few seconds for the disconnect to happen
    start_time = time.time()
    while time.time() - start_time < 3 and not spoof_blocked:
        client1.loop(0.1)

    if not spoof_blocked:
        print("[ERROR] Server did NOT block the unauthorized publish!")

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
    client2.username_pw_set(MQTT_USER, MQTT_PASS)
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
    client3.username_pw_set(MQTT_USER, MQTT_PASS)
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

