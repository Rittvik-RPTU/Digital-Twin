import json
import hashlib
import os
import shutil

API_KEYS_FILE = "pt_api_keys.json"
BACKUP_FILE = "pt_api_keys.plaintext.json"

def main():
    if not os.path.exists(API_KEYS_FILE):
        print(f"{API_KEYS_FILE} not found.")
        return

    # Backup the original file
    if not os.path.exists(BACKUP_FILE):
        shutil.copy2(API_KEYS_FILE, BACKUP_FILE)
        print(f"Backed up {API_KEYS_FILE} to {BACKUP_FILE}")

    with open(API_KEYS_FILE, "r") as f:
        data = json.load(f)

    hashed_data = {}
    for key, value in data.items():
        # Hash the key using SHA-256
        hashed_key = hashlib.sha256(key.encode('utf-8')).hexdigest()
        hashed_data[hashed_key] = value

    with open(API_KEYS_FILE, "w") as f:
        json.dump(hashed_data, f, indent=4)
        
    print(f"Successfully hashed API keys in {API_KEYS_FILE}")

if __name__ == "__main__":
    main()
