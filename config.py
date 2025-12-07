"""
Configuration for the Haggle Service Marketplace Backend.

API Keys Setup:
---------------
Create a .env file in the project root with:

    XAI_API_KEY=your_xai_api_key_here
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_api_key

Get your xAI API key from: https://console.x.ai/
Get your Supabase credentials from: https://supabase.com/dashboard
"""

import os
from dotenv import load_dotenv

load_dotenv()

# xAI (Grok) Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://podtjfttutrybvotsduh.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvZHRqZnR0dXRyeWJ2b3RzZHVoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUwOTgwMjksImV4cCI6MjA4MDY3NDAyOX0.OtP1eZ_TmiWyylcsf6HXndV3h44CHw-7rd0SBoEFlKE")

# Grok Model Settings (using xai_sdk)
GROK_MODEL = "grok-3-fast"  # Fast model for all operations

# Search Configuration
SEARCH_ALLOWED_DOMAINS = ["maps.google.com", "google.com/maps"]
MAX_PROVIDERS = 10

