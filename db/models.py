"""
Supabase models for the Haggle Service Marketplace.

Provider data is persisted to Supabase.
"""

from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Table name
PROVIDERS_TABLE = "providers"


class Provider:
    """
    Provider model - persisted to Supabase.
    
    Stores service providers found via Grok Fast Search.
    """
    
    def __init__(
        self,
        id: Optional[int] = None,
        service_provider: Optional[str] = None,
        phone_number: Optional[str] = None,
        context_answers: Optional[str] = None,
        house_address: Optional[str] = None,
        zip_code: Optional[str] = None,
        max_price: Optional[float] = None,
        job_id: Optional[str] = None,
        minimum_quote: Optional[float] = None,
        problem: Optional[str] = None,
        negotiated_price: Optional[float] = None,
        call_status: Optional[str] = None,
        call_transcript: Optional[str] = None
    ):
        self.id = id
        self.service_provider = service_provider
        self.phone_number = phone_number
        self.context_answers = context_answers
        self.house_address = house_address
        self.zip_code = zip_code
        self.max_price = max_price
        self.job_id = job_id
        self.minimum_quote = minimum_quote
        self.problem = problem
        self.negotiated_price = negotiated_price
        self.call_status = call_status
        self.call_transcript = call_transcript
    
    def __repr__(self):
        return f"<Provider(id={self.id}, service_provider='{self.service_provider}', phone_number='{self.phone_number}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert provider to dictionary for Supabase operations."""
        data = {}
        if self.service_provider is not None:
            data["service_provider"] = self.service_provider
        if self.phone_number is not None:
            data["phone_number"] = self.phone_number
        if self.context_answers is not None:
            data["context_answers"] = self.context_answers
        if self.house_address is not None:
            data["house_address"] = self.house_address
        if self.zip_code is not None:
            data["zip_code"] = self.zip_code
        if self.max_price is not None:
            data["max_price"] = self.max_price
        if self.job_id is not None:
            data["job_id"] = self.job_id
        if self.minimum_quote is not None:
            data["minimum_quote"] = self.minimum_quote
        if self.problem is not None:
            data["problem"] = self.problem
        if self.negotiated_price is not None:
            data["negotiated_price"] = self.negotiated_price
        if self.call_status is not None:
            data["call_status"] = self.call_status
        if self.call_transcript is not None:
            data["call_transcript"] = self.call_transcript
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Provider":
        """Create Provider from Supabase response dictionary."""
        return cls(
            id=data.get("id"),
            service_provider=data.get("service_provider"),
            phone_number=data.get("phone_number"),
            context_answers=data.get("context_answers"),
            house_address=data.get("house_address"),
            zip_code=data.get("zip_code"),
            max_price=data.get("max_price"),
            job_id=data.get("job_id"),
            minimum_quote=data.get("minimum_quote"),
            problem=data.get("problem"),
            negotiated_price=data.get("negotiated_price"),
            call_status=data.get("call_status"),
            call_transcript=data.get("call_transcript")
        )


def init_db():
    """
    Initialize the database by creating the providers table if it doesn't exist.
    
    Note: In Supabase, tables are typically created via the dashboard or migrations.
    This function is kept for compatibility but doesn't create tables programmatically.
    """
    print("✅ Supabase client initialized")
    print("⚠️  Note: Ensure the 'providers' table exists in your Supabase database.")
    print("   Required columns: id (serial), service_provider (text), phone_number (text),")
    print("   context_answers (text), house_address (text), zip_code (text), max_price (numeric),")
    print("   job_id (text), minimum_quote (numeric), problem (text),")
    print("   negotiated_price (numeric), call_status (text), call_transcript (text)")


def create_provider(provider: Provider) -> Provider:
    """
    Create a new provider in Supabase.
    
    Args:
        provider: Provider object to create
        
    Returns:
        Created Provider with ID from Supabase
    """
    data = provider.to_dict()
    response = supabase.table(PROVIDERS_TABLE).insert(data).execute()
    
    if response.data and len(response.data) > 0:
        return Provider.from_dict(response.data[0])
    else:
        raise Exception("Failed to create provider in Supabase")


def get_provider_by_id(provider_id: int) -> Optional[Provider]:
    """
    Get a provider by ID.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        Provider object or None if not found
    """
    response = supabase.table(PROVIDERS_TABLE).select("*").eq("id", provider_id).execute()
    
    if response.data and len(response.data) > 0:
        return Provider.from_dict(response.data[0])
    return None


def get_providers_by_job_id(job_id: str) -> List[Provider]:
    """
    Get all providers for a specific job.
    
    Args:
        job_id: Job ID
        
    Returns:
        List of Provider objects
    """
    response = supabase.table(PROVIDERS_TABLE).select("*").eq("job_id", job_id).execute()
    
    return [Provider.from_dict(item) for item in response.data] if response.data else []


def get_all_providers() -> List[Provider]:
    """
    Get all providers from the database.
    
    Returns:
        List of Provider objects
    """
    response = supabase.table(PROVIDERS_TABLE).select("*").execute()
    
    return [Provider.from_dict(item) for item in response.data] if response.data else []


def format_context_answers(answers: Dict[str, str], questions: List[Any]) -> str:
    """
    Format the answers to the 5 context questions into a paragraph.
    
    Args:
        answers: Dictionary of question IDs to answers (e.g., {"q1": "answer1", ...})
        questions: List of ClarifyingQuestion objects
        
    Returns:
        Formatted paragraph string
    """
    if not answers or not questions:
        return ""
    
    # Create a mapping of question IDs to question text
    question_map = {q.id: q.question for q in questions}
    
    # Build the paragraph
    paragraphs = []
    for q_id, answer in answers.items():
        question_text = question_map.get(q_id, q_id)
        paragraphs.append(f"{question_text} {answer}")
    
    return " ".join(paragraphs)


def update_provider_call_status(
    provider_id: int,
    call_status: str,
    negotiated_price: Optional[float] = None,
    call_transcript: Optional[str] = None
) -> Optional[Provider]:
    """
    Update a provider's call status and related fields.
    
    Args:
        provider_id: Provider ID
        call_status: New call status ('pending', 'in_progress', 'completed', 'failed')
        negotiated_price: Negotiated price if available
        call_transcript: Full call transcript if available
        
    Returns:
        Updated Provider object or None if not found
    """
    update_data = {"call_status": call_status}
    
    if negotiated_price is not None:
        update_data["negotiated_price"] = negotiated_price
    
    if call_transcript is not None:
        update_data["call_transcript"] = call_transcript
    
    response = supabase.table(PROVIDERS_TABLE).update(update_data).eq("id", provider_id).execute()
    
    if response.data and len(response.data) > 0:
        return Provider.from_dict(response.data[0])
    return None


# Note: format_problem_statement has been moved to services/grok_llm.py as an async function
# Import it from there: from services.grok_llm import format_problem_statement
