import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.gemini_client import GeminiClient

def test_module():
    print("Testing GeminiClient module directly...")
    client = GeminiClient(api_key="dummy")
    print(f"Configured: {client.configured}")
    
    idea = "A simple todo app"
    enhanced = client.enhance_idea(idea)
    print(f"Enhanced Title: {enhanced.get('title')}")
    
    prd = client.generate_prd(enhanced)
    print(f"PRD generated: {prd.get('prd') is not None}")
    if not prd.get('prd'):
        print(f"PRD Error: {prd}")

if __name__ == "__main__":
    test_module()
