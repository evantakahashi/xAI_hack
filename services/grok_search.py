"""
OpenAI Web Search Service for finding service providers.

Uses OpenAI's Responses API with web_search tool.
Docs: https://platform.openai.com/docs/guides/tools-web-search
"""

import os
import re
import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from openai import OpenAI

from config import MAX_PROVIDERS
from schemas import Job, ProviderCreate

# Load environment variables
load_dotenv()

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Thread pool for running synchronous SDK calls
_executor = ThreadPoolExecutor(max_workers=2)


def build_search_prompt(job: Job) -> str:
    """
    Construct a search prompt from the Job JSON.
    
    Args:
        job: The complete Job object with all clarifications
        
    Returns:
        A detailed search prompt for finding providers
    """
    prompt = f"""Find {job.task} services near zip code {job.zip_code}.

Search the web for local {job.task}s and provide a list with:
1. Business name
2. Phone number

Format each result as: NAME | PHONE

Find up to {MAX_PROVIDERS} providers near {job.zip_code}."""

    return prompt


def _sync_search_providers(job: Job) -> List[ProviderCreate]:
    """
    Synchronous implementation of provider search using OpenAI web search.
    Called from thread pool to avoid blocking async event loop.
    """
    search_prompt = build_search_prompt(job)
    
    print(f"\n[OpenAI Search] Query:\n{search_prompt}\n", flush=True)
    
    try:
        # Initialize OpenAI Client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        print("[OpenAI Search] Calling web_search tool...", flush=True)
        
        # Create response using web search tool
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=search_prompt,
        )
        
        # Get the output text
        full_response = response.output_text
        
        print(f"\n[OpenAI Search] Response received ({len(full_response)} chars)")
        print(f"\n{full_response}\n", flush=True)
        
        # Parse providers from response
        providers = parse_provider_response(full_response, job.id)
        
        return providers if providers else _fallback_providers(job)
        
    except Exception as e:
        print(f"OpenAI Search API exception: {e}")
        return _fallback_providers(job)


async def search_providers(job: Job) -> List[ProviderCreate]:
    """
    Search for service providers using OpenAI web search.
    
    Runs the synchronous SDK in a thread pool to avoid blocking.
    
    Args:
        job: The complete Job object
        
    Returns:
        List of ProviderCreate objects with name, phone
    """
    # Use fallback if no API key is configured
    if not OPENAI_API_KEY:
        print("⚠️  No OPENAI_API_KEY set - using fallback providers")
        return _fallback_providers(job)
    
    # Run synchronous SDK call in thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _sync_search_providers, job)


def parse_provider_response(content: str, job_id: str) -> List[ProviderCreate]:
    """
    Parse the response into ProviderCreate objects.
    
    Handles multiple formats:
    - NAME | PHONE
    - NAME - PHONE  
    - **NAME** | PHONE
    - 1. NAME | PHONE
    
    Args:
        content: Raw response content
        job_id: The job ID to associate with providers
        
    Returns:
        List of ProviderCreate objects
    """
    providers = []
    lines = content.strip().split("\n")
    
    # Phone number regex - matches (xxx) xxx-xxxx, xxx-xxx-xxxx, etc.
    phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header-like lines
        if "name" in line.lower() and "phone" in line.lower():
            continue
        if line.startswith("---") or line.startswith("==="):
            continue
            
        # Try to find a phone number in the line
        phone_match = phone_pattern.search(line)
        if not phone_match:
            continue
            
        phone = phone_match.group()
        
        # Extract name - everything before the phone number, cleaned up
        name_part = line[:phone_match.start()]
        
        # Clean up the name
        name = name_part.strip()
        # Remove common prefixes/formatting
        name = re.sub(r'^[\d]+[.\)]\s*', '', name)  # Remove "1." or "1)"
        name = re.sub(r'^\*+', '', name)  # Remove leading asterisks
        name = re.sub(r'\*+$', '', name)  # Remove trailing asterisks
        name = re.sub(r'^[-|:]\s*', '', name)  # Remove leading dash/pipe/colon
        name = re.sub(r'[-|:]\s*$', '', name)  # Remove trailing dash/pipe/colon
        name = name.strip()
        
        # Skip if name is empty or too short
        if not name or len(name) < 3:
            continue
        
        # Skip if name looks like a header
        if name.lower() in ["name", "business", "provider", "company"]:
            continue
            
        providers.append(ProviderCreate(
            job_id=job_id,
            name=name,
            phone=phone
        ))
    
    return providers[:MAX_PROVIDERS]


def _fallback_providers(job: Job) -> List[ProviderCreate]:
    """
    Fallback provider data for development/testing when API is unavailable.
    
    Returns realistic-looking mock data based on the task type.
    """
    task = job.task.lower()
    zip_code = job.zip_code
    
    mock_providers = {
        "plumber": [
            ("Reliable Plumbing Services", "(408) 555-0101", 150.0),
            ("Quick Drain Solutions", "(408) 555-0102", 125.0),
            ("Bay Area Master Plumbers", "(408) 555-0103", 175.0),
            ("24/7 Emergency Plumbing", "(408) 555-0104", 200.0),
            ("Budget Plumbing Co.", "(408) 555-0105", 100.0),
        ],
        "electrician": [
            ("Bright Spark Electric", "(408) 555-0201", 175.0),
            ("Safe Home Electrical", "(408) 555-0202", 150.0),
            ("PowerUp Electricians", "(408) 555-0203", 200.0),
            ("Circuit Masters", "(408) 555-0204", 165.0),
            ("Volt Electric Services", "(408) 555-0205", 140.0),
        ],
        "house cleaner": [
            ("Sparkle Clean Services", "(408) 555-0301", 120.0),
            ("Maid Perfect", "(408) 555-0302", 100.0),
            ("Home Fresh Cleaning", "(408) 555-0303", 95.0),
            ("Deep Clean Pros", "(408) 555-0304", 150.0),
            ("Tidy Home Services", "(408) 555-0305", 110.0),
        ],
        "painter": [
            ("Pro Coat Painters", "(408) 555-0401", 300.0),
            ("Fresh Paint Co.", "(408) 555-0402", 250.0),
            ("Color Masters Painting", "(408) 555-0403", 275.0),
            ("Premium Painting Services", "(408) 555-0404", 350.0),
            ("Budget Paint Pros", "(408) 555-0405", 200.0),
        ],
    }
    
    # Get task-specific or default providers
    default_providers = [
        ("Local Service Pro #1", "(408) 555-0001", 150.0),
        ("Trusted Handyman Services", "(408) 555-0002", 125.0),
        ("Quick Fix Solutions", "(408) 555-0003", 175.0),
        ("Reliable Home Services", "(408) 555-0004", 140.0),
        ("Expert Service Co.", "(408) 555-0005", 160.0),
    ]
    
    provider_list = mock_providers.get(task, default_providers)
    
    return [
        ProviderCreate(
            job_id=job.id,
            name=name,
            phone=phone
        )
        for name, phone, _ in provider_list
    ]
