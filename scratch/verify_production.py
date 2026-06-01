import sys
import requests
import time
import random

def verify_production(base_url):
    print(f"=== Starting Production Verification for {base_url} ===")
    
    # Random suffix for the test user
    suffix = random.randint(1000, 9999)
    test_email = f"prod_test_{suffix}@gitaai.com"
    test_password = "securepassword123"
    
    print(f"\n[1] Authentication Test")
    print(f"  -> Attempting Signup: {test_email}")
    
    signup_resp = requests.post(f"{base_url}/auth/signup", json={
        "full_name": "Prod Test User",
        "email": test_email,
        "password": test_password
    })
    
    if signup_resp.status_code == 200:
        print("  ✅ Signup Successful")
    elif signup_resp.status_code == 400 and "Email already registered" in signup_resp.text:
        print("  ✅ User exists, continuing to login")
    else:
        print(f"  ❌ Signup Failed: {signup_resp.status_code} - {signup_resp.text}")
        return
        
    print("  -> Attempting Login")
    login_resp = requests.post(f"{base_url}/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    
    if login_resp.status_code != 200:
        print(f"  ❌ Login Failed: {login_resp.status_code} - {login_resp.text}")
        return
        
    data = login_resp.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    
    if access_token and refresh_token:
        print("  ✅ Login Successful (Access & Refresh tokens received)")
    else:
        print("  ❌ Missing tokens in login response!")
        return

    print("\n[2] Token Refresh Test")
    refresh_resp = requests.post(f"{base_url}/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    if refresh_resp.status_code == 200:
        new_access = refresh_resp.json().get("access_token")
        if new_access:
            print("  ✅ Token Refresh Successful")
            access_token = new_access
        else:
            print("  ❌ Token Refresh failed to return new access token")
    else:
        print(f"  ❌ Token Refresh Request Failed: {refresh_resp.status_code} - {refresh_resp.text}")

    print("\n[3] Dashboard Health Audit Test (PostgreSQL & API Check)")
    headers = {"Authorization": f"Bearer {access_token}"}
    health_resp = requests.get(f"{base_url}/health/dashboard", headers=headers)
    
    if health_resp.status_code == 200:
        health_data = health_resp.json()
        print(f"  ✅ Health Audit Reached")
        print(f"  -> DB Read: {health_data.get('postgres_read')}")
        print(f"  -> Wellness API: {health_data.get('wellness_api')}")
        print(f"  -> Abhyasa API: {health_data.get('abhyasa_api')}")
        
        if health_data.get('overall_status') == 'PASS':
            print("  ✅ Backend is fully healthy and PostgreSQL is connected.")
        else:
            print(f"  ❌ Backend Health Audit Failed: {health_data.get('failing_endpoint')}")
    else:
        print(f"  ❌ Health Audit Endpoint Failed: {health_resp.status_code}")

    print("\n[4] Chat Intelligence Test")
    print("  -> Testing normal query (Should return verse)")
    chat_resp_1 = requests.post(f"{base_url}/chat/send", headers=headers, json={
        "text": "I am worried about my future and failing exams.",
        "voice_mode": False
    })
    
    if chat_resp_1.status_code == 200:
        print("  ✅ Chat Query 1 successful.")
        resp_json = chat_resp_1.json().get("text", {})
        if resp_json.get("chapter"):
            print(f"     -> Returned Verse: {resp_json.get('chapter')}.{resp_json.get('verse_number')}")
        else:
            print("     -> No verse returned.")
    else:
        print(f"  ❌ Chat Query 1 failed: {chat_resp_1.status_code}")
        
    print("  -> Testing gratitude (Should NOT return verse)")
    chat_resp_2 = requests.post(f"{base_url}/chat/send", headers=headers, json={
        "text": "Thank you, that was very helpful.",
        "voice_mode": False
    })
    
    if chat_resp_2.status_code == 200:
        print("  ✅ Chat Query 2 successful.")
        resp_json = chat_resp_2.json().get("text", {})
        if not resp_json.get("chapter"):
            print("     -> Correctly omitted verse for gratitude.")
        else:
            print("     ❌ Incorrectly returned verse for gratitude.")
    else:
        print(f"  ❌ Chat Query 2 failed: {chat_resp_2.status_code}")

    print("\n=== Verification Complete ===")
    print("To check UI elements (Dashboard blank states, Intro video replay, Mobile Responsiveness), please open the app in a browser.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_production.py <live_railway_url>")
        sys.exit(1)
        
    url = sys.argv[1].rstrip("/")
    verify_production(url)
