"""
Grok LLM Service for task inference and clarifying question generation.

Uses xAI's official SDK: https://docs.x.ai/docs/guides/chat
"""

import os
from typing import List, Dict, Union
from dotenv import load_dotenv

from xai_sdk import Client
from xai_sdk.chat import user, system

from config import XAI_API_KEY

# Load environment variables
load_dotenv()


async def infer_task(query: str) -> str:
    """
    Use Grok LLM to infer the service task from a user query.
    
    Args:
        query: User's free text query (e.g., "fix my toilet")
        
    Returns:
        Inferred task type (e.g., "plumber", "electrician", "cleaner")
    """
    # Use fallback if no API key is configured
    if not XAI_API_KEY:
        print("⚠️  No XAI_API_KEY set - using fallback task inference")
        return _fallback_infer_task(query)
    
    system_prompt = """You are a service task classifier. Given a user's request, 
identify the type of service professional needed. 

Respond with ONLY a single word or short phrase for the service type, such as:
- plumber
- electrician  
- house cleaner
- painter
- handyman
- HVAC technician
- locksmith
- carpenter
- landscaper
- appliance repair
- pest control
- roofer
- moving company
- auto mechanic

Be specific but concise. Just the service type, nothing else."""

    try:
        # Initialize xAI Client
        client = Client(api_key=XAI_API_KEY)
        
        # Create Chat
        chat = client.chat.create(model="grok-3-fast")
        
        # Add messages
        chat.append(system(system_prompt))
        chat.append(user(f"What type of service professional is needed for: {query}"))
        
        # Get response
        full_response = ""
        for response, chunk in chat.stream():
            if chunk.content:
                full_response += chunk.content
        
        task = full_response.strip().lower()
        return task
        
    except Exception as e:
        print(f"Grok API exception: {e}")
        return _fallback_infer_task(query)


def _fallback_infer_task(query: str) -> str:
    """Fallback task inference when API is unavailable."""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["toilet", "pipe", "leak", "faucet", "drain", "plumb"]):
        return "plumber"
    elif any(word in query_lower for word in ["electric", "outlet", "wire", "light", "switch"]):
        return "electrician"
    elif any(word in query_lower for word in ["clean", "maid", "tidy"]):
        return "house cleaner"
    elif any(word in query_lower for word in ["paint", "wall"]):
        return "painter"
    elif any(word in query_lower for word in ["ac", "hvac", "heat", "air condition", "furnace"]):
        return "HVAC technician"
    elif any(word in query_lower for word in ["lock", "key", "door"]):
        return "locksmith"
    elif any(word in query_lower for word in ["lawn", "yard", "garden", "tree"]):
        return "landscaper"
    elif any(word in query_lower for word in ["roof", "shingle", "gutter"]):
        return "roofer"
    elif any(word in query_lower for word in ["move", "moving", "relocat"]):
        return "moving company"
    elif any(word in query_lower for word in ["car", "auto", "vehicle", "brake", "oil"]):
        return "auto mechanic"
    else:
        return "handyman"


async def generate_clarifying_questions(
    task: str,
    query: str,
    zip_code: str,
    date_needed: str,
    price_limit: Union[float, str]
) -> List[Dict[str, str]]:
    """
    Generate up to 5 clarifying questions to better understand the job.
    
    Rules:
    - Max 5 questions
    - Do NOT ask for zip code, date needed, or price again
    - Keep questions minimal and necessary
    - No duplicate questions
    
    Args:
        task: Inferred task type
        query: Original user query
        zip_code: Already provided
        date_needed: Already provided
        price_limit: Already provided
        
    Returns:
        List of question dicts with 'id' and 'question' keys
    """
    # Use fallback if no API key is configured
    if not XAI_API_KEY:
        print("⚠️  No XAI_API_KEY set - using fallback questions")
        return _fallback_questions(task)
    
    system_prompt = """You are a service request specialist helping to understand job requirements.

Generate 3-5 clarifying questions to better understand the specific job needs.

IMPORTANT RULES:
1. Do NOT ask about location, zip code, or address - already provided
2. Do NOT ask about timing, date, or schedule - already provided  
3. Do NOT ask about budget or price - already provided
4. Keep questions specific to the actual work needed
5. Questions should help a service provider give an accurate estimate
6. Be concise - one clear question per line
7. Maximum 5 questions

Respond with ONLY the questions, one per line, numbered 1-5."""

    user_prompt = f"""Service type: {task}
User's request: "{query}"

Generate clarifying questions to understand this job better."""

    try:
        # Initialize xAI Client
        client = Client(api_key=XAI_API_KEY)
        
        # Create Chat
        chat = client.chat.create(model="grok-3-fast")
        
        # Add messages
        chat.append(system(system_prompt))
        chat.append(user(user_prompt))
        
        # Get response
        full_response = ""
        for response, chunk in chat.stream():
            if chunk.content:
                full_response += chunk.content
        
        content = full_response.strip()
        
        # Parse questions from response
        questions = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            # Remove numbering like "1.", "1)", "1:"
            for prefix in [f"{i+1}.", f"{i+1})", f"{i+1}:"]:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            # Also handle any number prefix
            if line and line[0].isdigit():
                parts = line.split(".", 1)
                if len(parts) > 1:
                    line = parts[1].strip()
                else:
                    parts = line.split(")", 1)
                    if len(parts) > 1:
                        line = parts[1].strip()
            
            if line and len(questions) < 5:
                questions.append({
                    "id": f"q{len(questions) + 1}",
                    "question": line
                })
        
        return questions if questions else _fallback_questions(task)
        
    except Exception as e:
        print(f"Grok API exception: {e}")
        return _fallback_questions(task)


def _fallback_questions(task: str) -> List[Dict[str, str]]:
    """Fallback questions when API is unavailable."""
    task_questions = {
        "plumber": [
            {"id": "q1", "question": "What is the specific issue you're experiencing?"},
            {"id": "q2", "question": "Is water actively leaking right now?"},
            {"id": "q3", "question": "How old is the fixture or pipe with the issue?"},
            {"id": "q4", "question": "Have you tried any fixes yourself?"},
            {"id": "q5", "question": "Is this affecting multiple fixtures?"}
        ],
        "electrician": [
            {"id": "q1", "question": "What electrical issue are you experiencing?"},
            {"id": "q2", "question": "Is this a new installation or a repair?"},
            {"id": "q3", "question": "Are any outlets or switches not working?"},
            {"id": "q4", "question": "Have you experienced any power outages or tripped breakers?"},
            {"id": "q5", "question": "What is the age of your home's electrical system?"}
        ],
        "house cleaner": [
            {"id": "q1", "question": "How many bedrooms and bathrooms need cleaning?"},
            {"id": "q2", "question": "What is the approximate square footage?"},
            {"id": "q3", "question": "Is this a one-time deep clean or regular service?"},
            {"id": "q4", "question": "Do you have pets?"},
            {"id": "q5", "question": "Are there any specific areas that need extra attention?"}
        ],
        "painter": [
            {"id": "q1", "question": "Is this interior or exterior painting?"},
            {"id": "q2", "question": "How many rooms or what square footage needs painting?"},
            {"id": "q3", "question": "Do you already have the paint or need it purchased?"},
            {"id": "q4", "question": "Are there any repairs needed before painting?"},
            {"id": "q5", "question": "What is the current condition of the walls?"}
        ]
    }
    
    # Default questions for any other task
    default_questions = [
        {"id": "q1", "question": "Can you describe the issue in more detail?"},
        {"id": "q2", "question": "Is this an urgent/emergency situation?"},
        {"id": "q3", "question": "Have you had this issue before?"},
        {"id": "q4", "question": "Is there anything else the service provider should know?"},
        {"id": "q5", "question": "Do you have any specific requirements or preferences?"}
    ]
    
    return task_questions.get(task, default_questions)
