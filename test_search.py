#!/usr/bin/env python3
"""Quick test of xai_sdk web_search"""

import os
import sys
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search, x_search

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

print("Starting test...")
print(f"API Key: {os.getenv('XAI_API_KEY')[:20]}...")

client = Client(api_key=os.getenv("XAI_API_KEY"))

print("Creating chat with grok-4-1-fast...")
chat = client.chat.create(
    model="grok-4-1-fast",
    tools=[
        web_search(),
        x_search(),
        web_search(allowed_domains=["google.com"])
    ],
)

print("Sending query...")
chat.append(user("Find phone numbers of plumbers near zip code 95126"))

print("Streaming response...")
for response, chunk in chat.stream():
    if chunk.tool_calls:
        for tool in chunk.tool_calls:
            print(f"[TOOL] {tool.function.name}")
    if chunk.content:
        print(chunk.content, end="", flush=True)

print("\n")
print("Done!")
print(f"Sources: {response.citations}")

