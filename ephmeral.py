import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

SESSION_REQUEST_URL = "https://api.x.ai/v1/realtime/client_secrets"

@app.post("/session")
async def create_session():
    api_key = os.getenv("GROK_API_KEY")
    
    if not api_key:
        return JSONResponse(
            content={"error": "Missing XAI_API_KEY in environment variables"}, 
            status_code=500
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SESSION_REQUEST_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "expires_after": {"seconds": 300}
                }
            )
            data = response.json()
            return JSONResponse(content=data, status_code=response.status_code)
        
        except httpx.RequestError as e:
            return JSONResponse(
                content={"error": f"Request failed: {str(e)}"}, 
                status_code=500
            )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
