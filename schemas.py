"""
Pydantic schemas for the Haggle Service Marketplace.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from enum import Enum
import uuid


class JobStatus(str, Enum):
    COLLECTING_INFO = "collecting_info"
    READY_FOR_SEARCH = "ready_for_search"
    SEARCHED = "searched"


# ============== Request Schemas ==============

class StartJobRequest(BaseModel):
    """Request to start a new job."""
    query: str = Field(..., description="User's free text query, e.g. 'fix my toilet'")
    house_address: str = Field(..., description="Full house address")
    zip_code: str = Field(..., description="User's ZIP code")
    price_limit: Union[float, str] = Field(..., description="Dollar amount or 'no_limit'")
    date_needed: str = Field(..., description="Date needed, e.g. '2025-12-10'")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "fix my toilet",
                "house_address": "123 Main St, San Jose, CA 95126",
                "zip_code": "95126",
                "price_limit": 250,
                "date_needed": "2025-12-10"
            }
        }


class CompleteJobRequest(BaseModel):
    """Request to complete a job with clarification answers."""
    job_id: str = Field(..., description="The job ID returned from start-job")
    answers: Dict[str, str] = Field(..., description="Answers to clarifying questions")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc123",
                "answers": {
                    "q1": "The toilet is constantly running",
                    "q2": "Standard toilet, not smart",
                    "q3": "First floor bathroom"
                }
            }
        }


# ============== Job Schema (In-Memory) ==============

class ClarifyingQuestion(BaseModel):
    """A clarifying question for the job."""
    id: str
    question: str


class Job(BaseModel):
    """
    Job object - NOT stored in DB, lives in memory/session.
    Will be passed to voice agent in Phase 2.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_query: str
    task: str = ""
    house_address: str
    zip_code: str
    date_needed: str
    price_limit: Union[float, str]
    clarifications: Dict[str, Any] = Field(default_factory=dict)
    questions: List[ClarifyingQuestion] = Field(default_factory=list)
    status: JobStatus = JobStatus.COLLECTING_INFO

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "original_query": "fix my toilet",
                "task": "plumber",
                "zip_code": "95126",
                "date_needed": "2025-12-10",
                "price_limit": 250,
                "clarifications": {
                    "q1": "The toilet is constantly running",
                    "q2": "Standard toilet"
                },
                "questions": [
                    {"id": "q1", "question": "What is the specific issue with your toilet?"},
                    {"id": "q2", "question": "What type of toilet do you have?"}
                ],
                "status": "collecting_info"
            }
        }


# ============== Provider Schema ==============

class ProviderBase(BaseModel):
    """Base provider data from search results."""
    name: str
    phone: Optional[str] = None


class ProviderCreate(ProviderBase):
    """Provider data for creating a new provider record."""
    job_id: str
    raw_result: Dict[str, Any] = Field(default_factory=dict)


class Provider(ProviderBase):
    """Full provider record from database."""
    id: int
    job_id: str
    raw_result: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ============== Response Schemas ==============

class StartJobResponse(BaseModel):
    """Response from starting a job."""
    job_id: str
    task: str
    questions: List[ClarifyingQuestion]

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "task": "plumber",
                "questions": [
                    {"id": "q1", "question": "What is the specific issue with your toilet?"},
                    {"id": "q2", "question": "Is your toilet running constantly or leaking?"},
                    {"id": "q3", "question": "How old is your toilet?"},
                    {"id": "q4", "question": "Have you noticed any water damage around the toilet?"},
                    {"id": "q5", "question": "Is this an emergency or can it wait a day?"}
                ]
            }
        }


class CompleteJobResponse(BaseModel):
    """Response from completing a job with providers."""
    job: Job
    providers: List[Provider]

    class Config:
        json_schema_extra = {
            "example": {
                "job": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "original_query": "fix my toilet",
                    "task": "plumber",
                    "zip_code": "95126",
                    "date_needed": "2025-12-10",
                    "price_limit": 250,
                    "clarifications": {
                        "q1": "The toilet is constantly running",
                        "q2": "Standard toilet, about 10 years old"
                    },
                    "questions": [],
                    "status": "searched"
                },
                "providers": [
                    {
                        "id": 1,
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Mike's Plumbing Services",
                        "phone": "(408) 555-1234",
                        "raw_result": {}
                    },
                    {
                        "id": 2,
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Bay Area Plumbers",
                        "phone": "(408) 555-5678",
                        "raw_result": {}
                    }
                ]
            }
        }

