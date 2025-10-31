import asyncio
import websockets
import json

async def test_copilot_bridge():
    uri = "ws://localhost:8765"  # WebSocket URL

    # Test prompt that should trigger Jira tool usage
    test_prompt = "What is the status of Jira issue CMU-105?"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to Copilot Bridge WebSocket")
            print(f"Sending request: {test_prompt}")

            # Send the request
            message = {
                "type": "copilot_request",
                "prompt": test_prompt,
                "requestId": "test-001"
            }

            await websocket.send(json.dumps(message))
            print("Request sent, waiting for response...")

            # Wait for response
            response = await websocket.recv()
            result = json.loads(response)

            print("✅ Success!")
            print(f"Response: {result.get('response', 'No response')}")

    except websockets.exceptions.ConnectionClosedError:
        print("❌ WebSocket connection closed unexpectedly")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_copilot_bridge())