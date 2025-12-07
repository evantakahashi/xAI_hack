# app.py
import os
import json
import base64
import audioop
import asyncio
import uvicorn
import websockets
from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv
from supabase import create_client, Client as SupabaseClient

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

# provider keys: id, service_provider, problem, phone_number, context_answers, zip_code, max_price, job_id, house_address

def generate_prompt(provider: dict) -> str:
    """Injects the raw context_answers directly into the system prompt."""
    return f"""
YOU ARE a homeowner in zip code {provider['zip_code']} calling for service.
{provider['problem']}.
YOU ARE NOT an AI. You are a real person speaking to {provider['service_provider']} for the first time.
Your tone should be casual, direct, and slightly cost-conscious.
Refer to the following context if needed: {provider['context_answers']}

1. You must begin the call with: "Hi, is this {provider['service_provider']}?" After receiving a response, state the problem you are calling for.
2. After confirming the technician can help, you must ask for a price estimate.
3. Your task is to secure the lowest possible price, using *${provider['max_price']}** as a target range. Use common, human-like negotiation tactics to encourage the technician to drop their initial quote.
4. Agreeing to a price up to ${provider['max_price']} is acceptable if they will not budge lower.

You must end the call based on the outcome of the negotiation:
    - OPTION 1 (No Agreement): If no price was agreed upon, use a variation of: "Thank you for the info. I need to think about it and will call you back."
    - OPTION 2 (Price Agreed): If a price at or below ${provider['max_price']} was agreed upon, use a variation of: "Thank you for your help! I will reach out to you again shortly."
"""

def remove_last_two_asterisks(name: str) -> str:
    """
    Find the first star (*) and remove that star and everything after it.
    If no star is found, return the name.
    """
    if "*" in name:
        return name.split("*")[0]
    else:
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
    """1. TRIGGER: Fetches rows and fires off calls in parallel"""
    
    # Fetch all providers for this job
    response = supabase.table("providers").select("*").eq("job_id", job_id).execute()
    providers = response.data
    
    if not providers:
        return {"error": "No providers found"}
    
    for provider in providers:
        provider['service_provider'] = remove_last_two_asterisks(provider['service_provider'])

    # Fire and forget
    for provider in providers:
        background_tasks.add_task(trigger_call, provider)
        
    return {"status": "started", "count": len(providers)}

@app.post("/twiml")
async def get_twiml(provider_id: str):
    """2. HANDOFF: Tells Twilio to connect audio to our WebSocket"""
    response = VoiceResponse()
    connect = Connect()
    # Pass the ID forward to the WebSocket
    stream = connect.stream(url=f"wss://{DOMAIN}/media-stream")
    stream.parameter(name="provider_id", value=provider_id) 
    
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """3. BRAIN: The Audio Bridge"""
    await websocket.accept()
    
    transcript = []

    # Connect to Grok
    async with websockets.connect(GROK_URL, additional_headers={"Authorization": f"Bearer {API_KEY}"}) as grok_ws:
        
        # Stream Loop
        stream_sid = None
        provider = None
        
        async def receive_from_twilio():
            nonlocal stream_sid, provider
            try:
                while True:
                    msg = await websocket.receive_text()
                    data = json.loads(msg)
                    
                    if data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        custom_params = data['start']['customParameters']
                        provider_id = custom_params.get('provider_id')
                        
                        # FETCH DATA: Get the full context fresh from DB
                        data = supabase.table("providers").select("*").eq("id", provider_id).single().execute()
                        provider = data.data
                        
                        
                        # Initialize Session
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
                        
                        
                    elif data['event'] == 'media':
                        # Transcode Twilio (Mulaw 8k) -> Grok (PCM 24k)
                        mulaw = base64.b64decode(data['media']['payload'])
                        pcm_8k = audioop.ulaw2lin(mulaw, 2)
                        pcm_24k, _ = audioop.ratecv(pcm_8k, 2, 1, 8000, 24000, None)
                        
                        await grok_ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": base64.b64encode(pcm_24k).decode('utf-8')
                        }))
            except Exception:
                pass # Call ended

        async def send_to_twilio():
            try:
                async for msg in grok_ws:
                    event = json.loads(msg)
                    event_type = event.get('type')
                    if event_type== 'response.output_audio.delta':
                        # Transcode Grok (PCM 24k) -> Twilio (Mulaw 8k)
                        pcm_24k = base64.b64decode(event['delta'])
                        pcm_8k, _ = audioop.ratecv(pcm_24k, 2, 1, 24000, 8000, None)
                        mulaw = audioop.lin2ulaw(pcm_8k, 2)
                        
                        if stream_sid:
                            await websocket.send_json({
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": base64.b64encode(mulaw).decode('utf-8')}
                            })
                        # Track transcript - User speech (input from Twilio)
                    elif event_type == 'conversation.item.input_audio_transcription.completed':
                        user_text = event.get('transcript', '')
                        if user_text:
                            transcript.append({
                                "role": "user",
                                "text": user_text
                            })
                            print(f"[USER]: {user_text}")
                    
                    # Track transcript - Assistant response (multiple possible event types)
                    elif event_type == 'response.audio_transcript.done':
                        assistant_text = event.get('transcript', '')
                        if assistant_text:
                            transcript.append({
                                "role": "assistant",
                                "text": assistant_text
                            })
                            print(f"[ASSISTANT]: {assistant_text}")
                    
                    elif event_type == 'response.text.done':
                        text = event.get('text', '')
                        if text:
                            transcript.append({
                                "role": "assistant",
                                "text": text
                            })
                            print(f"[ASSISTANT]: {text}")
                    
                    # Check response.done for comprehensive transcript data
                    elif event_type == 'response.done':
                        response_data = event.get('response', {})
                        output = response_data.get('output', [])
                        
                        for item in output:
                            if item.get('type') == 'message':
                                content = item.get('content', [])
                                for content_item in content:
                                    if content_item.get('type') == 'text':
                                        text = content_item.get('text', '')
                                        if text and not any(t.get('text') == text and t.get('role') == 'assistant' for t in transcript):
                                            transcript.append({
                                                "role": "assistant",
                                                "text": text
                                            })
                                            print(f"[ASSISTANT]: {text}")
                                    elif content_item.get('type') == 'audio':
                                        # Check if there's a transcript in the audio item
                                        audio_transcript = content_item.get('transcript', '')
                                        if audio_transcript and not any(t.get('text') == audio_transcript and t.get('role') == 'assistant' for t in transcript):
                                            transcript.append({
                                                "role": "assistant",
                                                "text": audio_transcript
                                            })
                                            print(f"[ASSISTANT]: {audio_transcript}")
                    
                    # Check conversation.item.created for assistant messages
                    elif event_type == 'conversation.item.created':
                        item = event.get('item', {})
                        if item.get('role') == 'assistant':
                            content = item.get('content', [])
                            for content_item in content:
                                if content_item.get('type') == 'text':
                                    text = content_item.get('text', '')
                                    if text:
                                        transcript.append({
                                            "role": "assistant",
                                            "text": text
                                        })
                                        print(f"[ASSISTANT]: {text}")
                                elif content_item.get('type') == 'audio':
                                    audio_transcript = content_item.get('transcript', '')
                                    if audio_transcript:
                                        transcript.append({
                                            "role": "assistant",
                                            "text": audio_transcript
                                        })
                                        print(f"[ASSISTANT]: {audio_transcript}")
            except Exception:
                pass

        await asyncio.gather(receive_from_twilio(), send_to_twilio())
        
        
    # Print the complete transcript at the end
    print("\n" + "="*80)
    print("COMPLETE CONVERSATION TRANSCRIPT")
    print("="*80)
    for i, entry in enumerate(transcript, 1):
        role = entry['role'].upper()
        text = entry['text']
        print(f"{i}. [{role}]: {text}")
    print("="*80 + "\n")
    
    print(f"🏁 Call Ended: {provider['service_provider']}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6000)
