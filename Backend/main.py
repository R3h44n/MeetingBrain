import os
import io
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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

# Initialize the official Mistral client
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

@app.websocket("/ws")
async def websocket_endpoint(client_ws: WebSocket):
    await client_ws.accept()
    print("Frontend connected! Ready for audio chunks.")
    
    session_audio = bytearray()
    is_transcribing = False  # <-- Our new Traffic Light flag!
    
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
                            await client_ws.send_text(transcript_text)
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