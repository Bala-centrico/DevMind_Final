"""
Test script for DevMindAPI
"""
import requests
import json
import sys

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_copilot_chat(prompt: str):
    """Test Copilot chat endpoint"""
    print(f"\n🔍 Testing Copilot chat with prompt: '{prompt}'")
    try:
        response = requests.post(
            f"{API_URL}/api/v1/copilot/chat",
            json={"prompt": prompt, "timeout": 30}
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_empty_prompt():
    """Test with empty prompt (should fail validation)"""
    print("\n🔍 Testing empty prompt (should fail)...")
    try:
        response = requests.post(
            f"{API_URL}/api/v1/copilot/chat",
            json={"prompt": ""}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 422  # Validation error expected
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("DevMindAPI Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    # Test 2: Empty prompt validation
    results.append(("Empty Prompt Validation", test_empty_prompt()))
    
    # Test 3: Simple Copilot query
    results.append(("Simple Query", test_copilot_chat("What is Python?")))
    
    # Test 4: Code generation
    results.append(("Code Generation", test_copilot_chat(
        "Write a Python function to reverse a string"
    )))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Return exit code
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
