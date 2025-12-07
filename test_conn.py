import asyncio
import os
import websockets
from dotenv import load_dotenv

load_dotenv()

async def connect_to_realtime():
    url = "wss://api.x.ai/v1/realtime"
    api_key = os.getenv("GROK_API_KEY")
    print("API_KEY", api_key)

    if not api_key:
        print("Error: GROK_API_KEY not found.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print(f"Connecting to {url}...")

    try:
        # Establish the connection
        async with websockets.connect(url, additional_headers=headers) as ws:
            # This block runs when the connection is open
            print("Connected with API key authentication")

            # Example: Keep the connection open to listen for messages
            async for message in ws:
                print(f"Received: {message}")

    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    # Run the async event loop
    asyncio.run(connect_to_realtime())
