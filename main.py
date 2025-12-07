"""
Haggle Service Marketplace Backend - Phase 1

FastAPI application for service provider discovery.
Uses Grok LLM for task inference and Grok Fast Search for provider lookup.

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid

from schemas import (
    StartJobRequest,
    StartJobResponse,
    CompleteJobRequest,
    CompleteJobResponse,
    Job,
    JobStatus,
    ClarifyingQuestion,
    Provider as ProviderSchema
)
from db.models import (
    Provider,
    init_db,
    create_provider,
    get_providers_by_job_id,
    get_all_providers,
    format_context_answers
)
from services.grok_llm import infer_task, generate_clarifying_questions
from services.grok_search import search_providers

# Initialize FastAPI app
app = FastAPI(
    title="Haggle Service Marketplace",
    description="Phase 1: Service provider discovery using Grok LLM and Fast Search",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (jobs don't persist to DB)
# In production, use Redis or similar for session storage
jobs_store: Dict[str, Job] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("✅ Database initialized")
    print("🚀 Haggle Service Marketplace API is running!")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Haggle Service Marketplace",
        "version": "1.0.0",
        "status": "running",
        "phase": 1
    }


@app.get("/api/health")
async def health_check():
    """API health check."""
    return {"status": "healthy"}


# ============== Main Endpoints ==============

@app.post("/api/start-job", response_model=StartJobResponse)
async def start_job(request: StartJobRequest):
    """
    Start a new job request.
    
    Flow:
    1. Call Grok LLM to infer the task type
    2. Generate up to 5 clarifying questions
    3. Create Job object in memory
    4. Return job_id, task, and questions
    
    Example Request:
    ```json
    {
        "query": "fix my toilet",
        "house_address": "123 Main St, San Jose, CA 95126",
        "zip_code": "95126",
        "price_limit": 250,
        "date_needed": "2025-12-10"
    }
    ```
    
    Example Response:
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "task": "plumber",
        "questions": [
            {"id": "q1", "question": "What is the specific issue with your toilet?"},
            {"id": "q2", "question": "Is the toilet running constantly or leaking?"},
            {"id": "q3", "question": "How old is your toilet?"},
            {"id": "q4", "question": "Have you noticed any water damage?"},
            {"id": "q5", "question": "Is this an emergency?"}
        ]
    }
    ```
    """
    try:
        # Step 1: Infer task from query using Grok LLM
        task = await infer_task(request.query)
        
        # Step 2: Generate clarifying questions
        questions_data = await generate_clarifying_questions(
            task=task,
            query=request.query,
            zip_code=request.zip_code,
            date_needed=request.date_needed,
            price_limit=request.price_limit
        )
        
        # Convert to ClarifyingQuestion objects
        questions = [
            ClarifyingQuestion(id=q["id"], question=q["question"])
            for q in questions_data
        ]
        
        # Step 3: Create Job object (in-memory, not DB)
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            original_query=request.query,
            task=task,
            house_address=request.house_address,
            zip_code=request.zip_code,
            date_needed=request.date_needed,
            price_limit=request.price_limit,
            questions=questions,
            status=JobStatus.COLLECTING_INFO
        )
        
        # Store job in memory
        jobs_store[job_id] = job
        
        return StartJobResponse(
            job_id=job_id,
            task=task,
            questions=questions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting job: {str(e)}")


@app.post("/api/complete-job", response_model=CompleteJobResponse)
async def complete_job(request: CompleteJobRequest):
    """
    Complete a job with clarification answers and search for providers.
    
    Flow:
    1. Retrieve job from memory
    2. Merge clarification answers into job
    3. Build search prompt from job JSON
    4. Call Grok Fast Search
    5. Normalize and save providers to Supabase
    6. Return job + providers
    
    Example Request:
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "answers": {
            "q1": "The toilet is constantly running",
            "q2": "Yes, water runs non-stop",
            "q3": "About 10 years old",
            "q4": "No water damage visible",
            "q5": "Not an emergency, can wait a day"
        }
    }
    ```
    
    Example Response:
    ```json
    {
        "job": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "original_query": "fix my toilet",
            "task": "plumber",
            "zip_code": "95126",
            "date_needed": "2025-12-10",
            "price_limit": 250,
            "clarifications": {
                "q1": "The toilet is constantly running",
                "q2": "Yes, water runs non-stop"
            },
            "questions": [...],
            "status": "searched"
        },
        "providers": [
            {
                "id": 1,
                "job_id": "550e8400-...",
                "name": "Reliable Plumbing Services",
                "phone": "(408) 555-0101",
                "estimated_price": 150.0,
                "raw_result": {}
            },
            ...
        ]
    }
    ```
    """
    # Step 1: Retrieve job from memory
    job = jobs_store.get(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
    
    try:
        # Step 2: Merge clarification answers
        job.clarifications = request.answers
        job.status = JobStatus.READY_FOR_SEARCH
        
        # Step 3 & 4: Search for providers using Grok Fast Search
        provider_creates = await search_providers(job)
        
        # Format context answers as a paragraph
        context_answers_text = format_context_answers(request.answers, job.questions)
        
        # Parse price_limit to get max_price
        max_price = None
        if isinstance(job.price_limit, (int, float)):
            max_price = float(job.price_limit)
        elif isinstance(job.price_limit, str) and job.price_limit.lower() != "no_limit":
            try:
                max_price = float(job.price_limit)
            except ValueError:
                pass
        
        # Step 5: Save providers to Supabase
        saved_providers = []
        for pc in provider_creates:
            db_provider = Provider(
                job_id=pc.job_id,
                service_provider=pc.name,
                phone_number=pc.phone,
                context_answers=context_answers_text,
                house_address=job.house_address,
                zip_code=job.zip_code,
                max_price=max_price,
                raw_result=pc.raw_result
            )
            
            created_provider = create_provider(db_provider)
            
            saved_providers.append(ProviderSchema(
                id=created_provider.id,
                job_id=created_provider.job_id,
                name=created_provider.service_provider,
                phone=created_provider.phone_number,
                raw_result=created_provider.raw_result or {}
            ))
        
        # Update job status
        job.status = JobStatus.SEARCHED
        jobs_store[request.job_id] = job
        
        return CompleteJobResponse(
            job=job,
            providers=saved_providers
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing job: {str(e)}")


# ============== Debug/Development Endpoints ==============

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get a job by ID (for debugging)."""
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job


@app.get("/api/providers")
async def list_providers():
    """List all providers in database (for debugging)."""
    providers = get_all_providers()
    return [
        ProviderSchema(
            id=p.id,
            job_id=p.job_id,
            name=p.service_provider,
            phone=p.phone_number,
            raw_result=p.raw_result or {}
        )
        for p in providers
    ]


@app.get("/api/providers/{job_id}")
async def get_providers_by_job(job_id: str):
    """Get all providers for a specific job."""
    providers = get_providers_by_job_id(job_id)
    return [
        ProviderSchema(
            id=p.id,
            job_id=p.job_id,
            name=p.service_provider,
            phone=p.phone_number,
            raw_result=p.raw_result or {}
        )
        for p in providers
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

