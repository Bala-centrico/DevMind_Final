"""
Test script for DevMindAPI Multi-Model support
Tests all available AI models with sample prompts
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any
import time

API_BASE_URL = "http://localhost:8000"

# Test prompts for different scenarios
TEST_PROMPTS = {
    "simple": "Say hello in one sentence.",
    "code": "Write a Python function to calculate factorial of a number.",
    "explain": "Explain what async/await means in Python in 2-3 sentences.",
    "creative": "Write a haiku about programming."
}


class APITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results = []
    
    async def test_health(self):
        """Test health endpoint"""
        print("\n" + "="*70)
        print("TESTING HEALTH ENDPOINT")
        print("="*70)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    data = await response.json()
                    
                    print(f"✓ Status: {data['status']}")
                    print(f"✓ VS Code Bridge: {'Connected' if data['bridge_connected'] else 'Not Connected'}")
                    print(f"✓ Available Models:")
                    for model, available in data['available_models'].items():
                        status = "✓" if available else "❌"
                        print(f"  {status} {model}")
                    
                    return data
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return None
    
    async def test_list_models(self):
        """Test models listing endpoint"""
        print("\n" + "="*70)
        print("TESTING MODELS LIST")
        print("="*70)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/models") as response:
                    data = await response.json()
                    
                    print(f"✓ Total Models: {data['total_models']}")
                    print(f"✓ Available: {data['available_count']}")
                    print(f"\n{'Model Key':<25} {'Provider':<15} {'Available':<10} {'Cost':<15}")
                    print("-" * 70)
                    
                    for model in data['models']:
                        status = "✓" if model['available'] else "❌"
                        print(f"{model['key']:<25} {model['provider']:<15} {status:<10} {model['cost_type']:<15}")
                    
                    return data
        except Exception as e:
            print(f"❌ Models list failed: {e}")
            return None
    
    async def test_model(self, model_key: str, prompt: str, prompt_name: str = ""):
        """Test a specific model with a prompt"""
        print(f"\n{'-'*70}")
        print(f"Testing: {model_key}")
        if prompt_name:
            print(f"Prompt Type: {prompt_name}")
        print(f"Prompt: {prompt}")
        print(f"{'-'*70}")
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "prompt": prompt,
                    "model": model_key,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                async with session.post(
                    f"{self.base_url}/api/v1/ai/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)
                ) as response:
                    elapsed = time.time() - start_time
                    data = await response.json()
                    
                    if data['success']:
                        print(f"✓ Success (took {elapsed:.2f}s)")
                        print(f"Provider: {data['provider']}")
                        print(f"Response ({len(data['response'])} chars):")
                        print(f"{data['response'][:300]}...")
                        
                        self.results.append({
                            "model": model_key,
                            "prompt": prompt_name or "custom",
                            "success": True,
                            "time": elapsed,
                            "length": len(data['response'])
                        })
                    else:
                        print(f"❌ Failed: {data.get('error', 'Unknown error')}")
                        self.results.append({
                            "model": model_key,
                            "prompt": prompt_name or "custom",
                            "success": False,
                            "error": data.get('error', 'Unknown')
                        })
                    
                    return data
                    
        except asyncio.TimeoutError:
            print(f"❌ Timeout after {time.time() - start_time:.2f}s")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    async def test_all_models(self, prompt_type: str = "simple"):
        """Test all available models with a specific prompt"""
        print("\n" + "="*70)
        print(f"TESTING ALL MODELS WITH '{prompt_type.upper()}' PROMPT")
        print("="*70)
        
        # Get available models
        models_data = await self.test_list_models()
        if not models_data:
            print("Could not retrieve models list")
            return
        
        prompt = TEST_PROMPTS.get(prompt_type, TEST_PROMPTS["simple"])
        
        # Test each available model
        for model in models_data['models']:
            if model['available']:
                await self.test_model(model['key'], prompt, prompt_type)
                await asyncio.sleep(1)  # Be nice to the APIs
            else:
                print(f"\n❌ Skipping {model['key']} (not available)")
    
    def print_summary(self):
        """Print summary of all tests"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        if not self.results:
            print("No tests were run")
            return
        
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        print(f"Total Tests: {len(self.results)}")
        print(f"✓ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        
        if successful:
            avg_time = sum(r['time'] for r in successful) / len(successful)
            print(f"\nAverage Response Time: {avg_time:.2f}s")
            print(f"\nFastest: {min(successful, key=lambda r: r['time'])['model']} ({min(r['time'] for r in successful):.2f}s)")
            print(f"Slowest: {max(successful, key=lambda r: r['time'])['model']} ({max(r['time'] for r in successful):.2f}s)")


async def interactive_test():
    """Interactive testing mode"""
    tester = APITester()
    
    print("\n" + "="*70)
    print("DevMindAPI Multi-Model Interactive Tester")
    print("="*70)
    
    while True:
        print("\n" + "="*70)
        print("Choose an option:")
        print("1. Test health endpoint")
        print("2. List available models")
        print("3. Test specific model")
        print("4. Test all available models")
        print("5. Run comprehensive test suite")
        print("6. Show test summary")
        print("0. Exit")
        print("="*70)
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            print("\nGoodbye!")
            break
        
        elif choice == "1":
            await tester.test_health()
        
        elif choice == "2":
            await tester.test_list_models()
        
        elif choice == "3":
            model = input("Enter model key (e.g., openai-gpt4): ").strip()
            prompt = input("Enter prompt: ").strip()
            await tester.test_model(model, prompt)
        
        elif choice == "4":
            print("\nSelect prompt type:")
            for i, (key, prompt) in enumerate(TEST_PROMPTS.items(), 1):
                print(f"{i}. {key}: {prompt}")
            
            prompt_choice = input("\nEnter choice (1-4): ").strip()
            prompt_types = list(TEST_PROMPTS.keys())
            
            try:
                prompt_type = prompt_types[int(prompt_choice) - 1]
                await tester.test_all_models(prompt_type)
            except (ValueError, IndexError):
                print("Invalid choice")
        
        elif choice == "5":
            print("\nRunning comprehensive test suite...")
            await tester.test_health()
            await tester.test_list_models()
            
            for prompt_name, prompt in TEST_PROMPTS.items():
                models_data = await tester.test_list_models()
                if models_data:
                    # Test first available model with each prompt
                    for model in models_data['models'][:3]:  # Test first 3
                        if model['available']:
                            await tester.test_model(model['key'], prompt, prompt_name)
                            break
            
            tester.print_summary()
        
        elif choice == "6":
            tester.print_summary()
        
        else:
            print("Invalid choice")


async def quick_test():
    """Quick test of basic functionality"""
    tester = APITester()
    
    print("\n" + "="*70)
    print("DevMindAPI Multi-Model Quick Test")
    print("="*70)
    
    # Test health
    await tester.test_health()
    
    # List models
    models_data = await tester.test_list_models()
    
    if models_data:
        # Test first available model
        for model in models_data['models']:
            if model['available']:
                await tester.test_model(
                    model['key'],
                    TEST_PROMPTS['simple'],
                    'simple'
                )
                break
    
    tester.print_summary()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(quick_test())
    else:
        asyncio.run(interactive_test())
