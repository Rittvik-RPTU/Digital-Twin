import requests
import json

base_url = "http://cps-dttest.cs.rptu.de:8088"
login_url = f"{base_url}/login"
projects_url = f"{base_url}/projects"

print("Logging in to university backend...")
try:
    payload = {"username": "admin", "password": "admin"}
    # Try JSON post
    r = requests.post(login_url, json=payload, timeout=5)
    print(f"Login Response Code: {r.status_code}")
    print(f"Login Response: {r.text}")
    
    # Fallback to form data if JSON doesn't succeed
    if r.status_code != 200:
        r = requests.post(login_url, data=payload, timeout=5)
        print(f"Login (Form) Response Code: {r.status_code}")
        print(f"Login (Form) Response: {r.text}")
        
    token = ""
    try:
        token = r.json().get("barrierString", "")
    except:
        token = r.text
        
    print(f"Extracted token: {token}")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r_proj = requests.get(projects_url, headers=headers, timeout=5)
    print(f"Projects Response Code: {r_proj.status_code}")
    projects = r_proj.json()
    print("\nAvailable projects on university server:")
    for p in projects:
        print(f" - Name: {p.get('name')}, ID: {p.get('id') or p.get('@id')}")
except Exception as e:
    print(f"Error querying backend: {e}")
