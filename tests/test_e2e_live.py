import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print("Testing /health...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

def test_enhance_idea():
    print("\nTesting /api/enhance-idea...")
    payload = {
        "gemini_key": "dummy_key", # Will fall back to simulation if invalid/missing
        "app_idea": "A to-do list app that gamifies tasks",
        "tech_preferences": "Python, React"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/enhance-idea", json=payload)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Success: {data.get('success')}")
        if data.get('enhanced_idea'):
            print(f"Title: {data['enhanced_idea'].get('title')}")
        else:
            print("No enhanced idea returned")
        return data.get('enhanced_idea')
    except Exception as e:
        print(f"Failed: {e}")
        return None

def test_generate_prd(sample_enhanced_idea):
    print("\nTesting /api/generate-prd...")
    if not sample_enhanced_idea:
        print("Skipping PRD test (no enhanced idea)")
        return

    payload = {
        "gemini_key": "dummy_key",
        "enhanced_idea": sample_enhanced_idea
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/generate-prd", json=payload)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Success: {data.get('success')}")
        if not data.get('success'):
            print(f"Message: {data.get('message')}")
        
        if data.get('prd'):
            print(f"Epics: {len(data['prd'].get('epics', []))}")
        else:
            print("No PRD returned")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    if test_health():
        idea = test_enhance_idea()
        test_generate_prd(idea)
