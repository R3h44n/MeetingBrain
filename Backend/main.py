import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow React to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

systemPrompt = """You are a precise action item extractor for technical and business meetings.

You must catch action items even when phrased with domain-specific jargon:
- Engineering: "I'll double-check the conservation of energy calculations before the next sprint"
- Finance: "We need to reconcile the EBITDA variance against Q3 actuals by Thursday"
- Legal: "Someone should review the indemnification clause in section 4.2"

Rules:
1. Normalize the task into a clear, imperative sentence
2. If the assignee says "I", use "speaker"
3. Include due date if mentioned, else null
4. Return ONLY a raw JSON array — no markdown fences, no explanation

Schema: [{"task": "...", "assignee": "...", "due": "..."}]"""

# Initialize the official Mistral client
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

DEBOUNCE_SECONDS = 4.0  # Wait 4s of transcript silence before extracting

def run_extraction(full_transcript: str) -> list:
    response = mistral_client.chat.complete(
        model="ministral-8b-latest",
        messages=[
            {"role": "system", "content": systemPrompt},
            {"role": "user", "content": f"Extract action items:\n\n{full_transcript}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1024,
    )
    raw = response.choices[0].message.content.strip()
    parsed = json.loads(raw)
    if isinstance(parsed, list):
        return parsed
    for v in parsed.values():
        if isinstance(v, list):
            return v
    return []

@app.websocket("/ws")
async def websocket_endpoint(client_ws: WebSocket):
    await client_ws.accept()
    print("Frontend connected! Ready for audio chunks.")
    
    session_audio = bytearray()
    full_transcript_parts = []
    is_transcribing = False
    debounce_handle = None          # Holds the pending extraction timer

    async def trigger_extraction():
        """Called after DEBOUNCE_SECONDS of no new transcript chunks."""
        combined = " ".join(full_transcript_parts)
        if not combined.strip():
            return
        print(f"\n--- Debounce fired. Extracting from {len(combined)} chars ---")
        try:
            items = await asyncio.to_thread(run_extraction, combined)
            print(json.dumps(items, indent=2))
            await client_ws.send_text(json.dumps({
                "type": "action_items",
                "items": items,
                "source_length": len(combined)
            }))
        except Exception as e:
            print(f"Extraction error: {e}")

    def schedule_extraction():
        """Reset the debounce timer every time a new transcript arrives."""
        nonlocal debounce_handle
        if debounce_handle:
            debounce_handle.cancel()
        loop = asyncio.get_event_loop()
        debounce_handle = loop.call_later(
            DEBOUNCE_SECONDS,
            lambda: asyncio.create_task(trigger_extraction())
        )
    
    try:
        while True:
            # 1. ALWAYS catch the audio chunks instantly (so React doesn't lag)
            audio_bytes = await client_ws.receive_bytes()
            session_audio.extend(audio_bytes)
            
            # 2. Only send to Mistral if the traffic light is GREEN
            if not is_transcribing and len(session_audio) > 0:
                is_transcribing = True  # Turn the light RED
                
                # Take a thread-safe snapshot of the audio accumulated so far
                audio_snapshot = bytes(session_audio)
                
                def transcribe_snapshot():
                    response = mistral_client.audio.transcriptions.complete(
                        model="voxtral-mini-latest", 
                        file={
                            "content": audio_snapshot, 
                            "file_name": "meeting.webm"
                        }
                    )
                    return response.text

                # 3. Create a background task to handle the API call
                async def process_and_send():
                    nonlocal is_transcribing
                    try:
                        transcript_text = await asyncio.to_thread(transcribe_snapshot)
                        if transcript_text:
                            print(f"Transcribed: {transcript_text}")
                            full_transcript_parts.append(transcript_text)

                            await client_ws.send_text(json.dumps({
                                "type": "transcript",
                                "text": transcript_text
                            }))

                            # Reset the debounce timer
                            schedule_extraction()
                    except Exception as api_err:
                        print(f"Mistral API Error: {api_err}")
                    finally:
                        is_transcribing = False # Turn the light GREEN again!

                # Fire off the background task
                asyncio.create_task(process_and_send())
                
    except WebSocketDisconnect:
        print("Frontend disconnected.")
    except Exception as e:
        print(f"System Error: {e}")
