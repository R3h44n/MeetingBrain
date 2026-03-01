import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from pydantic import BaseModel
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

# ---------------------------------------------------------
# PROMPTS
# ---------------------------------------------------------
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

QA_SYSTEM_PROMPT = """You are an intelligent meeting assistant. 
Answer the user's question using ONLY the provided meeting transcript. 
If the answer is not contained in the transcript, state clearly that it has not been discussed yet. 
Do not hallucinate or use outside knowledge."""

# ---------------------------------------------------------
# CLIENT & CONFIG
# ---------------------------------------------------------
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
DEBOUNCE_SECONDS = 2.0  

# ---------------------------------------------------------
# BLOCK 3: ACTION ITEM EXTRACTION (Ministral 8B)
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# BLOCK 4: CHAT WITH MEETING (Mistral Large 3)
# ---------------------------------------------------------
class AskRequest(BaseModel):
    transcript: str
    question: str

class AskResponse(BaseModel):
    answer: str
    model: str

@app.post("/ask", response_model=AskResponse)
async def ask_about_transcript(body: AskRequest):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    user_message = (
        f"MEETING TRANSCRIPT:\n"
        f"{'─' * 60}\n"
        f"{body.transcript.strip()}\n"
        f"{'─' * 60}\n\n"
        f"QUESTION: {body.question.strip()}"
    )

    try:
        response = await mistral_client.chat.complete_async(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": QA_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3, 
            max_tokens=2048,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Mistral API error: {str(e)}")

    answer = response.choices[0].message.content.strip()
    return AskResponse(answer=answer, model="mistral-large-latest")

# ---------------------------------------------------------
# BLOCK 1 & 2: REAL-TIME AUDIO WEBSOCKET (Voxtral Mini)
# ---------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(client_ws: WebSocket):
    await client_ws.accept()
    print("Frontend connected! Ready for audio chunks.")
    
    session_audio = bytearray()
    latest_transcript = ""  
    last_extracted_transcript = ""  # The memory check variable
    is_transcribing = False
    debounce_handle = None  

    async def trigger_extraction():
        nonlocal latest_transcript, last_extracted_transcript
        
        # Guardrail 1: Don't extract if the transcript is empty
        if not latest_transcript.strip():
            return
            
        # Guardrail 2: Don't extract if nothing has changed!
        if latest_transcript == last_extracted_transcript:
            return
            
        # Update memory so we don't repeat this exact string
        last_extracted_transcript = latest_transcript
        
        print(f"\n--- Debounce fired. Extracting from {len(latest_transcript)} chars ---")
        try:
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
            
            # The 15KB threshold to prevent the 3310 decoding error
            if not is_transcribing and len(session_audio) > 15000:
                is_transcribing = True
                audio_snapshot = bytes(session_audio)
                
                async def process_and_send():
                    nonlocal is_transcribing, latest_transcript
                    try:
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