"""
Example usage of DevMindAPI
Demonstrates how to integrate the API into your Python applications
"""
import requests
import json
import time

class DevMindAPIClient:
    """Client for DevMindAPI - VS Code Copilot Bridge"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def check_health(self) -> dict:
        """Check if API and bridge are healthy"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def ask_copilot(self, prompt: str, timeout: int = 60) -> dict:
        """
        Send a prompt to Copilot and get response
        
        Args:
            prompt: The question or prompt to send
            timeout: Maximum time to wait for response (seconds)
            
        Returns:
            dict: Response from Copilot
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/copilot/chat",
            json={"prompt": prompt, "timeout": timeout}
        )
        response.raise_for_status()
        return response.json()
    
    def is_connected(self) -> bool:
        """Check if bridge is connected"""
        try:
            health = self.check_health()
            return health.get("bridge_connected", False)
        except:
            return False


def example_1_simple_question():
    """Example 1: Ask a simple question"""
    print("\n" + "="*60)
    print("Example 1: Simple Question")
    print("="*60)
    
    client = DevMindAPIClient()
    
    # Check connection
    if not client.is_connected():
        print("❌ Bridge not connected. Please start VS Code extension.")
        return
    
    # Ask a question
    result = client.ask_copilot("What is Python used for?")
    
    print(f"Prompt: {result['prompt']}")
    print(f"Response: {result['response']}")
    print(f"Success: {result['success']}")


def example_2_code_generation():
    """Example 2: Generate code"""
    print("\n" + "="*60)
    print("Example 2: Code Generation")
    print("="*60)
    
    client = DevMindAPIClient()
    
    prompt = "Write a Python function to calculate the nth Fibonacci number using recursion"
    result = client.ask_copilot(prompt)
    
    if result['success']:
        print(f"Generated Code:\n{result['response']}")
    else:
        print(f"Error: {result['error']}")


def example_3_code_review():
    """Example 3: Code review"""
    print("\n" + "="*60)
    print("Example 3: Code Review")
    print("="*60)
    
    client = DevMindAPIClient()
    
    code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total / len(numbers)
    """
    
    prompt = f"Review this code and suggest improvements:\n{code}"
    result = client.ask_copilot(prompt, timeout=30)
    
    if result['success']:
        print(f"Code Review:\n{result['response']}")
    else:
        print(f"Error: {result['error']}")


def example_4_multiple_questions():
    """Example 4: Ask multiple questions in sequence"""
    print("\n" + "="*60)
    print("Example 4: Multiple Questions")
    print("="*60)
    
    client = DevMindAPIClient()
    
    questions = [
        "What is FastAPI?",
        "What are the benefits of using FastAPI?",
        "How do I create a POST endpoint in FastAPI?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        result = client.ask_copilot(question, timeout=30)
        
        if result['success']:
            print(f"Answer: {result['response'][:200]}...")  # First 200 chars
        else:
            print(f"Error: {result['error']}")
        
        # Be nice to the API - small delay between requests
        if i < len(questions):
            time.sleep(1)


def example_5_error_handling():
    """Example 5: Proper error handling"""
    print("\n" + "="*60)
    print("Example 5: Error Handling")
    print("="*60)
    
    client = DevMindAPIClient()
    
    # Test 1: Empty prompt (should fail validation)
    try:
        result = client.ask_copilot("")
        print("❌ Should have raised an error for empty prompt")
    except requests.exceptions.HTTPError as e:
        print(f"✓ Correctly rejected empty prompt: {e.response.status_code}")
    
    # Test 2: Valid prompt
    try:
        result = client.ask_copilot("Hello, Copilot!")
        print(f"✓ Valid request succeeded: {result['success']}")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Valid request failed: {e}")
    
    # Test 3: Check health
    try:
        health = client.check_health()
        print(f"✓ Health check: {health['status']}, Bridge: {health['bridge_connected']}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")


def example_6_batch_processing():
    """Example 6: Batch process code files"""
    print("\n" + "="*60)
    print("Example 6: Batch Code Analysis")
    print("="*60)
    
    client = DevMindAPIClient()
    
    code_snippets = {
        "snippet1.py": "def add(a, b): return a + b",
        "snippet2.py": "for i in range(10): print(i)",
        "snippet3.py": "x = [i**2 for i in range(5)]"
    }
    
    for filename, code in code_snippets.items():
        print(f"\nAnalyzing {filename}...")
        prompt = f"Explain what this code does in one sentence: {code}"
        
        try:
            result = client.ask_copilot(prompt, timeout=20)
            if result['success']:
                print(f"  → {result['response']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("DevMindAPI - Example Usage")
    print("="*60)
    
    print("\nMake sure:")
    print("1. FastAPI is running (python main.py)")
    print("2. VS Code extension is activated")
    print("3. GitHub Copilot is enabled")
    
    input("\nPress Enter to continue...")
    
    try:
        # Run examples
        example_1_simple_question()
        example_2_code_generation()
        example_3_code_review()
        example_4_multiple_questions()
        example_5_error_handling()
        example_6_batch_processing()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to DevMindAPI")
        print("Please ensure the API is running: python main.py")
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
