"""
Configuration for the Haggle Service Marketplace Backend.

API Keys Setup:
---------------
Create a .env file in the project root with:

    XAI_API_KEY=your_xai_api_key_here
    DATABASE_URL=sqlite:///./haggle.db

Get your xAI API key from: https://console.x.ai/
"""

import os
from dotenv import load_dotenv

load_dotenv()

# xAI (Grok) Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./haggle.db")

# Grok Model Settings (using xai_sdk)
GROK_MODEL = "grok-3-fast"  # Fast model for all operations

# Search Configuration
SEARCH_ALLOWED_DOMAINS = ["maps.google.com", "google.com/maps"]
MAX_PROVIDERS = 10

