# app.py
import os
import sys
import json
import base64
import audioop
import asyncio
import uvicorn
import websockets
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, BackgroundTasks, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv
from supabase import create_client, Client as SupabaseClient
from services.grok_llm import extract_negotiated_price
from db.models import update_provider_call_status

load_dotenv()

app = FastAPI()

# Configuration
GROK_URL = "wss://api.x.ai/v1/realtime"
API_KEY = os.getenv("XAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DOMAIN = os.getenv("DOMAIN")

# Initialize Supabase
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_prompt(provider: dict) -> str:
    """Injects the raw context_answers directly into the system prompt."""
    return f"""
YOU ARE a homeowner in zip code {provider.get('zip_code', 'unknown')} calling for service.
{provider.get('problem', 'plumbing issue')}.
YOU ARE NOT an AI. You are a real person speaking to {provider.get('service_provider', 'the technician')} for the first time.
Your tone should be casual, direct, and slightly cost-conscious.
Refer to the following context if needed: {provider.get('context_answers', '')}

1. You must begin the call with: "Hi, is this {provider.get('service_provider', 'the technician')}?" After receiving a response, state the problem you are calling for.
2. After confirming the technician can help, you must ask for a price estimate.
3. Your task is to secure the lowest possible price, using *${provider.get('max_price', 200)}** as a target range. Use common, human-like negotiation tactics to encourage the technician to drop their initial quote.
4. Agreeing to a price up to ${provider.get('max_price', 200)} is acceptable if they will not budge lower.

You must end the call based on the outcome of the negotiation:
    - OPTION 1 (No Agreement): If no price was agreed upon, use a variation of: "Thank you for the info. I need to think about it and will call you back."
    - OPTION 2 (Price Agreed): If a price at or below ${provider.get('max_price', 200)} was agreed upon, use a variation of: "Thank you for your help! I will reach out to you again shortly."
"""

def remove_last_two_asterisks(name: str) -> str:
    if name and "*" in name:
        return name.split("*")[0]
    return name

async def trigger_call(provider: dict):
    """The actual Twilio API call running in background"""
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    try:
        # We pass provider_id in the URL so the next step knows who we are calling
        twiml_url = f"https://{DOMAIN}/twiml?provider_id={provider['id']}"
        client.calls.create(
            to=provider['phone_number'],
            from_=FROM_NUMBER,
            url=twiml_url
        )
        print(f"🚀 Dialing {provider['service_provider']} (ID: {provider['id']})...")
    except Exception as e:
        print(f"❌ Failed to dial {provider['service_provider']}: {e}")

@app.post("/start-job/{job_id}")
async def start_job(job_id: str, background_tasks: BackgroundTasks):
    response = supabase.table("providers").select("*").eq("job_id", job_id).execute()
    providers = response.data
    
    if not providers:
        return {"error": "No providers found"}
    
    for provider in providers:
        provider['service_provider'] = remove_last_two_asterisks(provider.get('service_provider', ''))

    for provider in providers:
        background_tasks.add_task(trigger_call, provider)
        
    return {"status": "started", "count": len(providers)}

@app.post("/twiml")
async def get_twiml(provider_id: str):
    response = VoiceResponse()
    connect = Connect()
    stream = connect.stream(url=f"wss://{DOMAIN}/media-stream")
    stream.parameter(name="provider_id", value=provider_id) 
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    
    transcript = []
    provider_id = None
    provider = None

    try:
        async with websockets.connect(GROK_URL, additional_headers={"Authorization": f"Bearer {API_KEY}"}) as grok_ws:
            
            stream_sid = None
            
            async def receive_from_twilio():
                nonlocal stream_sid, provider, provider_id
                try:
                    while True:
                        msg = await websocket.receive_text()
                        data = json.loads(msg)
                        
                        if data['event'] == 'start':
                            stream_sid = data['start']['streamSid']
                            custom_params = data['start']['customParameters']
                            provider_id = custom_params.get('provider_id')
                            
                            if provider_id:
                                try:
                                    update_provider_call_status(int(provider_id), "in_progress")
                                except Exception as e:
                                    print(f"⚠️  Failed to update call status: {e}")
                            
                            data = supabase.table("providers").select("*").eq("id", provider_id).single().execute()
                            provider = data.data
                            print(f"🔌 Connected to provider: {provider.get('service_provider')}")
                            
                            # 1. Configure the Session
                            await grok_ws.send(json.dumps({
                                "type": "session.update",
                                "session": {
                                    "voice": "Rex",
                                    "instructions": generate_prompt(provider),
                                    "turn_detection": {"type": "server_vad"},
                                    "audio": {
                                        "input": {"format": {"type": "audio/pcm", "rate": 24000}},
                                        "output": {"format": {"type": "audio/pcm", "rate": 24000}}
                                    }
                                }
                            }))
                            
                            # 2. TRIGGER THE GREETING (CRITICAL FIX)
                            # This tells Grok: "Generate audio for your first turn NOW"
                            await grok_ws.send(json.dumps({
                                "type": "response.create"
                            }))
                            
                        elif data['event'] == 'media':
                            mulaw = base64.b64decode(data['media']['payload'])
                            pcm_8k = audioop.ulaw2lin(mulaw, 2)
                            pcm_24k, _ = audioop.ratecv(pcm_8k, 2, 1, 8000, 24000, None)
                            
                            await grok_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": base64.b64encode(pcm_24k).decode('utf-8')
                            }))
                            
                except WebSocketDisconnect:
                    raise # Let the gather handle it
                except Exception as e:
                    # Ignore connection closed errors from Grok when shutting down
                    pass 

            async def send_to_twilio():
                nonlocal transcript
                try:
                    async for msg in grok_ws:
                        event = json.loads(msg)
                        event_type = event.get('type')
                        
                        if event_type== 'response.output_audio.delta':
                            pcm_24k = base64.b64decode(event['delta'])
                            pcm_8k, _ = audioop.ratecv(pcm_24k, 2, 1, 24000, 8000, None)
                            mulaw = audioop.lin2ulaw(pcm_8k, 2)
                            
                            if stream_sid:
                                await websocket.send_json({
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": base64.b64encode(mulaw).decode('utf-8')}
                                })

                        # CAPTURE TRANSCRIPT
                        elif event_type == 'conversation.item.input_audio_transcription.completed':
                            user_text = event.get('transcript', '')
                            if user_text:
                                transcript.append({"role": "user", "text": user_text})
                                print(f"[USER]: {user_text}")
                        
                        elif event_type == 'response.audio_transcript.done':
                            asst_text = event.get('transcript', '')
                            if asst_text:
                                transcript.append({"role": "assistant", "text": asst_text})
                                print(f"[ASSISTANT]: {asst_text}")
                        elif event_type == 'response.output_audio_transcript.done' or event_type == 'response.audio_transcript.done':
                            asst_text = event.get('transcript', '')
                            if asst_text:
                                transcript.append({"role": "assistant", "text": asst_text})
                                print(f"[ASSISTANT]: {asst_text}")

                        # 3. Capture ASSISTANT text (if any)
                        elif event_type == 'response.text.done':
                            text = event.get('text', '')
                            if text:
                                transcript.append({"role": "assistant", "text": text})
                                print(f"[ASSISTANT]: {text}")

                except Exception as e:
                    pass

            # Run both loops
            await asyncio.gather(receive_from_twilio(), send_to_twilio())

    except WebSocketDisconnect:
        print("🔌 Twilio Disconnected")
    except Exception as e:
        print(f"❌ Error in call loop: {e}")

    finally:
        # LOGGING AND DB UPDATE
        print("\n" + "="*80)
        print("COMPLETE CONVERSATION TRANSCRIPT")
        print("="*80)
        
        transcript_text = ""
        for i, entry in enumerate(transcript, 1):
            line = f"{i}. [{entry['role'].upper()}]: {entry['text']}"
            print(line)
            transcript_text += line + "\n"
        print("="*80 + "\n")
        
        negotiated_price = None
        if transcript:
            try:
                # Use your existing LLM service to parse the price
                negotiated_price = await extract_negotiated_price(transcript)
                print(f"💰 Negotiated Price: {negotiated_price}")
            except Exception as e:
                print(f"❌ Price extraction failed: {e}")
        
        if provider_id:
            try:
                status = "completed" if negotiated_price else "failed"
                update_provider_call_status(
                    int(provider_id),
                    status,
                    negotiated_price=negotiated_price,
                    call_transcript=transcript_text
                )
                print(f"✅ DB Updated for Provider {provider_id}")
            except Exception as e:
                print(f"❌ DB Update failed: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6000)
