# MeetingBrain 🧠

**Real-time meeting intelligence, automated task extraction, and contextual Q&A.** Built for the Mistral AI Hackathon.

MeetingBrain transforms raw meeting audio into structured, actionable data on the fly. By leveraging a custom full-duplex WebSocket architecture, it streams microphone data to a FastAPI backend, dynamically batches it for transcription, and uses multi-agent LLM logic to extract tasks and answer questions about the discussion.

## 🚀 Key Features

* **Zero-Latency Audio Streaming:** Captures microphone data via the browser's native Web Audio API and streams binary WebM chunks over WebSockets.
* **Live Transcription:** Uses a dynamic "snowballing" byte-buffer alongside async thread locks to achieve continuous transcription via Mistral's `voxtral-mini-latest` model without dropping SSL connections.
* **Real-time Action Item Extraction:** Implements a sliding context window powered by **Ministral 8B** (via JSON mode) to detect commitments, assignees, and deadlines as they are spoken.
* **Post-Meeting Q&A:** Integrates **Mistral Large 3** to act as a reasoning agent, allowing users to query the entire meeting transcript for deep context.

## 🛠 Tech Stack

**Frontend**
* Next.js & React
* Tailwind CSS
* Web Audio API & Native WebSockets

**Backend**
* Python & FastAPI
* Uvicorn (ASGI server)
* Mistral AI V2 Python SDK

**AI Models**
* Mistral `voxtral-mini-latest` (Speech-to-Text)
* Ministral 8B (Entity/JSON Extraction)
* Mistral Large 3 (Reasoning/Q&A)

---

## 💻 Local Setup Instructions

You will need two terminal windows to run the frontend and backend simultaneously.

### 1. Backend Setup
Navigate to the backend directory and set up your Python environment:

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
# Create a .env file in the backend directory and add: 
# MISTRAL_API_KEY=your_key_here

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
Navigate to the frontend directory:

```bash
# Install Node modules
npm install

# Start the Next.js development server
npm run dev
```

Open `http://localhost:3000` in your browser. Click "Start Meeting" and grant microphone permissions to begin streaming audio to the AI pipeline.