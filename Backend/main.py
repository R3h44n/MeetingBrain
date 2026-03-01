import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

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

# Back to just one client, because we are using native async now!
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

DEBOUNCE_SECONDS = 2.0  

# 1. Changed to an async function using complete_async
async def run_extraction(full_transcript: str) -> list:
    response = await mistral_client.chat.complete_async(
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
    latest_transcript = ""  
    is_transcribing = False
    debounce_handle = None  

    async def trigger_extraction():
        nonlocal latest_transcript
        if not latest_transcript.strip():
            return
        print(f"\n--- Debounce fired. Extracting from {len(latest_transcript)} chars ---")
        try:
            # 2. Native await instead of to_thread
            items = await run_extraction(latest_transcript)
            print(json.dumps(items, indent=2))
            await client_ws.send_text(json.dumps({
                "type": "action_items",
                "items": items,
                "source_length": len(latest_transcript)
            }))
        except Exception as e:
            print(f"Extraction error: {e}")

    def schedule_extraction():
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
            audio_bytes = await client_ws.receive_bytes()
            session_audio.extend(audio_bytes)
            
            if not is_transcribing and len(session_audio) > 0:
                is_transcribing = True
                audio_snapshot = bytes(session_audio)
                
                async def process_and_send():
                    nonlocal is_transcribing, latest_transcript
                    try:
                        # 3. Native async audio transcription! No threads needed.
                        response = await mistral_client.audio.transcriptions.complete_async(
                            model="voxtral-mini-latest", 
                            file={
                                "content": audio_snapshot, 
                                "file_name": "meeting.webm"
                            }
                        )
                        transcript_text = response.text
                        
                        if transcript_text:
                            latest_transcript = transcript_text
                            await client_ws.send_text(json.dumps({
                                "type": "transcript",
                                "text": transcript_text
                            }))
                            schedule_extraction()
                            
                    except Exception as api_err:
                        print(f"Mistral API Error: {api_err}")
                    finally:
                        is_transcribing = False 

                asyncio.create_task(process_and_send())
                
    except WebSocketDisconnect:
        print("Frontend disconnected.")
    except Exception as e:
        print(f"System Error: {e}")