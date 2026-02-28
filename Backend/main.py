import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins (perfect for local hackathon testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
# Note: Ensure your .env file has MISTRAL_API_KEY=your_actual_key
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
VOXTRAL_WS_URL = "wss://api.mistral.ai/v1/realtime"

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(client_ws: WebSocket):
    """The main endpoint the React frontend connects to."""
    await client_ws.accept()
    print("Frontend connected to FastAPI.")
    
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}

    try:
        # Establish the "uplink" to the Voxtral API
        async with websockets.connect(VOXTRAL_WS_URL, additional_headers=headers) as voxtral_ws:
            print("FastAPI connected to Voxtral API.")

            # Task 1: The Audio Uplink (React -> FastAPI -> Voxtral)
            async def forward_audio_to_voxtral():
                try:
                    while True:
                        # 1. Receive raw audio bytes from the browser
                        audio_bytes = await client_ws.receive_bytes()
                        
                        # 2. Encode to Base64 (Standard protocol for Realtime APIs)
                        base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
                        
                        # 3. Package and fire off to Voxtral
                        payload = {
                            "type": "input_audio_buffer.append",
                            "audio": base64_audio
                        }
                        await voxtral_ws.send(json.dumps(payload))
                except WebSocketDisconnect:
                    print("Frontend disconnected.")

            # Task 2: The Text Downlink (Voxtral -> FastAPI -> React)
            async def forward_text_to_client():
                try:
                    async for message in voxtral_ws:
                        data = json.loads(message)

                        print("VOXTRAL SAID:", data)
                        
                        # Voxtral sends various event types. We only care about the actual text.
                        if data.get("type") == "transcription.delta":
                            text_chunk = data.get("delta", "")
                            
                            # Push the text straight down the pipe to React
                            await client_ws.send_text(text_chunk)
                            
                except websockets.exceptions.ConnectionClosed:
                    print("Voxtral connection closed.")

            # Run both continuous streams simultaneously
            await asyncio.gather(
                forward_audio_to_voxtral(),
                forward_text_to_client()
            )

    except Exception as e:
        print(f"System Error: {e}")
        await client_ws.close()