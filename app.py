# main.py
import os
import json
import base64
import audioop
import asyncio
import uvicorn
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuration
GROK_URL = "wss://api.x.ai/v1/realtime"
API_KEY = os.getenv("GROK_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Simple In-Memory State for the Demo
CALL_CONTEXT = {
  "job_id": "toilet_fix_001",
  "user_profile": {
    "name": "Alex",
    "zipcode": "94588",
    "date": "2025-12-07"
  },
  "technical_details": {
    "problem": "Leaking water onto floor from base", # MAKE SURE THIS IS FORMATTED CORRECTLY FROM THEM
    "context": "The toilet is leaking water onto the floor from the base. The toilet is a standard porcelain toilet. The access notes are ground floor, street parking available."
  },
  "negotiation_state": {
    "max_ceiling": 250,
    "current_best_offer": None,  # Updates as calls happen
  },
  "call_list": [
    {"name": "Mario's Plumbing", "phone": "+1415..."}, # maybe add transcript 
    {"name": "Luigi's Leak Fix", "phone": "+1415..."}
  ]
}

def generate_advanced_prompt(context, current_technician_name):
    user = context['user_profile']
    tech = context['technical_details']
    state = context['negotiation_state']

    prompt = f"""
    TARGET: You are calling {current_technician_name}.
    CONTEXT: This is the FIRST time you are speaking to them. You have never called them before.

    CRITICAL OPENER (Say exactly this first):
    "Hi, is this {current_technician_name}?"

    Wait for confirmation before proceeding.

    IDENTITY:
    You are {user['name']}, a homeowner in zip code {user['zipcode']}.
    You are NOT an AI. You are a real person with a leak.
    Tone: Casual, direct, slightly cost-conscious. Use "Uh," "Um," "Yeah."

    SCENARIO:
    After they confirm their name, say:
    "I'm in {user['zipcode']} and {tech['problem']}. Is this something you can help with?"

    TECHNICAL CONTEXT (Use if asked):
    {tech['context']}

    NEGOTIATION STRATEGY (Your Goal: Get the absolute lowest price):
    
    STEP 1: GET THE NUMBER
    Ask: "What's the rough ballpark for that? Best case/worst case?"
    - If they refuse to quote: "I get it, but I have a tight budget. What's your call-out fee just to show up?"

    STEP 2: THE HAGGLE (If they give a price)
    
    Case A: Price is SIGNIFICANTLY BELOW ${state['max_ceiling']} (e.g. $50-$100 less)
    - Reaction: "Oh, that's actually great."
    - Action: "Can you confirm that includes parts and labor?"
    
    Case B: Price is NEAR Max Ceiling (Within $20 of ${state['max_ceiling']}) or AT Ceiling
    - Reaction: "Okay, that's decent, but I was really hoping to stay a bit lower than that."
    - Action: "If I booked you for tomorrow, could you do any better on the price?"
      - If YES: "Awesome. I need to double check my schedule, but I'll call you right back."
      - If NO: "Okay, fair enough. That's still a reasonable number. Let me think about it and call you back."

    Case C: Price is HIGH (Over ${state['max_ceiling']})
    - Reaction: "Oof, that's a bit steeper than I expected."
    - Action: "Is that your absolute best price? I was hoping to stay under ${state['max_ceiling']}."
      - If they drop price: Go to Case B logic.
      - If they stand firm: "Okay, I appreciate it, but that's probably out of my range. Thanks anyway"


    RULES:
    - Never accept the first price immediately. Always ask "Is that the best you can do?" once.
    - Keep answers short. Don't over-explain.
    """
    return prompt



@app.post("/make-call")
async def make_call(request: Request):
    """Trigger the outbound call via Twilio API"""
    data = await request.json()
    to_number = data.get("to_number")
    domain = data.get("domain") # passed from UI or hardcoded

    client = Client(TWILIO_SID, TWILIO_TOKEN)
    
    # Twilio will fetch the TwiML from this URL when the call connects
    url = f"https://{domain}/twiml_stream"
    
    call = client.calls.create(
        to=to_number,
        from_=FROM_NUMBER,
        url=url
    )
    return {"status": "calling", "call_sid": call.sid}

@app.post("/twiml_stream")
async def twiml_stream(request: Request):
    """Returns TwiML to tell Twilio: 'Connect this call to our WebSocket'"""
    # We need the host to know where to connect the websocket
    form_data = await request.form()
    host = request.headers.get("host")
    
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=f"wss://{host}/media-stream")
    response.append(connect)
    
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """The Core Bridge: Twilio <-> Your Server <-> Grok"""
    await websocket.accept()
    print("Twilio Connected")

    # Transcript tracking
    transcript = []
    
    instructions = generate_advanced_prompt(CALL_CONTEXT, "Mario's Plumbing")
    print("Instructions: ", instructions)

    # 1. Connect to Grok
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "GrokHackathonBot/1.0"
    }
    async with websockets.connect(GROK_URL, additional_headers=headers) as grok_ws:
        print("Grok Connected")

        # 2. Configure Grok Session
        session_config = {
            "type": "session.update",
            "session": {
                "voice": "Rex",
                "instructions": instructions,
                "turn_detection": {"type": "server_vad"},
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "audio": {
                    "input": {"format": {"type": "audio/pcm", "rate": 24000}},
                    "output": {"format": {"type": "audio/pcm", "rate": 24000}}
                }
            }
        }
        await grok_ws.send(json.dumps(session_config))

        # 3. Stream Handler
        stream_sid = None

        async def receive_from_twilio():
            nonlocal stream_sid
            try:
                while True:
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    if data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        
                    elif data['event'] == 'media':
                        # Twilio sends Mulaw 8000Hz
                        mulaw_chunk = base64.b64decode(data['media']['payload'])
                        
                        # Transcode: Mulaw 8k -> PCM 24k
                        # 1. Mulaw -> Linear16 (8k)
                        pcm_8k = audioop.ulaw2lin(mulaw_chunk, 2)
                        # 2. Resample 8k -> 24k
                        pcm_24k, _ = audioop.ratecv(pcm_8k, 2, 1, 8000, 24000, None)
                        
                        # Send to Grok
                        await grok_ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": base64.b64encode(pcm_24k).decode('utf-8')
                        }))
            except websockets.exceptions.WebSocketException:
                print("Twilio Disconnected")
            except Exception as e:
                print(f"Error from Twilio: {e}")

        async def send_to_twilio():
            try:
                async for message in grok_ws:
                    event = json.loads(message)
                    event_type = event.get('type', '')
                    
                    if event_type == 'response.output_audio.delta':
                        # Grok sends PCM 24000Hz
                        pcm_24k = base64.b64decode(event['delta'])
                        
                        # Transcode: PCM 24k -> Mulaw 8k
                        # 1. Resample 24k -> 8k
                        pcm_8k, _ = audioop.ratecv(pcm_24k, 2, 1, 24000, 8000, None)
                        # 2. Linear16 -> Mulaw
                        mulaw_chunk = audioop.lin2ulaw(pcm_8k, 2)
                        
                        if stream_sid:
                            await websocket.send_json({
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": base64.b64encode(mulaw_chunk).decode('utf-8')
                                }
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
                    
                    elif event_type == 'response.audio_transcript.delta':
                        # Accumulate deltas - we'll need to track this
                        pass
                    
                    elif event_type == 'response.text.done':
                        text = event.get('text', '')
                        if text:
                            transcript.append({
                                "role": "assistant",
                                "text": text
                            })
                            print(f"[ASSISTANT]: {text}")
                    
                    elif event_type == 'response.text.delta':
                        # Accumulate text deltas
                        pass
                    
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
                            
                    if event_type == 'input_audio_buffer.speech_started':
                        # Optional: Send "clear" to Twilio if you want to support barge-in
                        # await websocket.send_json({"event": "clear", "streamSid": stream_sid})
                        pass

            except Exception as e:
                print(f"Error from Grok: {e}")

        # Run both streams concurrently
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6000)
