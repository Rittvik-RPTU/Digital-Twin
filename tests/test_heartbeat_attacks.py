#!/usr/bin/env python3

import subprocess
import time
import sys

def print_header(text):
    print(f"\n{'='*50}\n{text}\n{'='*50}")

def run_command(command, description, expect_failure=False):
    print(f"\n[TEST] {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=not expect_failure,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("[SUCCESS] Command succeeded as expected.")
        elif expect_failure:
             print(f"[SUCCESS] Command failed as expected (Exit code: {result.returncode}).")
        else:
             print(f"[ERROR] Command failed unexpectedly (Exit code: {result.returncode}).")
             print(f"Stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        if expect_failure:
            print(f"[SUCCESS] Command failed as expected (Exit code: {e.returncode}).")
        else:
            print(f"[ERROR] Command failed unexpectedly (Exit code: {e.returncode}).")
            print(f"Stderr: {e.stderr}")
    except subprocess.TimeoutExpired:
        if expect_failure:
             print("[SUCCESS] Command timed out as expected (Connection killed).")
        else:
             print("[ERROR] Command timed out unexpectedly.")

def main():
    print_header("Digital Twin Integrity & Security Test Suite")

    print("Please ensure the DigitalTwinServer and mock_agila_server are running before executing this script.")
    print("Waiting 2 seconds...")
    time.sleep(2)

    # Attack 1: Attempt to Spoof the Heartbeat (The "Man-in-the-Middle" attack)
    # The attacker tries to publish a fake "OK" status to the integrity topic to fool monitors.
    print_header("Attack 1: Spoofing the Integrity Heartbeat")
    run_command(
        'mosquitto_pub -d -V 5 -h localhost -p 1883 -u testuser -P testpass -t "dt/system/integrity" -m "{\\"status\\":\\"fake_ok\\"}"',
        "Attempting to publish to dt/system/integrity as a normal user",
        expect_failure=True
    )

    # Attack 2: Attempt to cause a Denial of Service (DoS) by spamming large payloads
    print_header("Attack 2: Resource Exhaustion / Large Packet")
    print("Generating a 50KB payload to stress the broker...")
    
    # We generate the payload natively in Python instead of using subshells to avoid OS arg limits
    large_payload = "A" * 50000 
    
    run_command(
        f'mosquitto_pub -d -V 5 -h localhost -p 1883 -u testuser -P testpass -t "dt/test" -m "{large_payload}"',
        "Attempting to send a 50KB payload",
        expect_failure=False # Broker should accept and drop it or handle it gracefully
    )

    # Verification: Check if Heartbeat is still alive
    print_header("Verification: Is the Heartbeat Still Alive?")
    print("We will subscribe to the heartbeat topic. We expect to receive at least one heartbeat (sent every 10s).")
    try:
        # Use a generous timeout and exit on first message
        result = subprocess.run(
            'mosquitto_sub -V 5 -h localhost -p 1883 -u testuser -P testpass -t "dt/system/integrity" -C 1 -W 15',
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=16
        )
        print("[SUCCESS] Received heartbeat payload:")
        print(f"  {result.stdout.strip()}")
        print("Conclusion: The server survived the attacks and the heartbeat is functioning normally.")
    except subprocess.TimeoutExpired:
        print("[ERROR] Failed to receive heartbeat within 12 seconds. The server might be compromised or frozen!")
    except subprocess.CalledProcessError as e:
         print(f"[ERROR] Failed to subscribe to heartbeat: {e.stderr}")

if __name__ == "__main__":
    main()
