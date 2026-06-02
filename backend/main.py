from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
from dotenv import load_dotenv
from src.agents.orchestrator import OrchestratorAgent
import groq
import re

load_dotenv()

app = FastAPI(title="Euro Trip Planner API")

# Allow CORS for Vercel Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    prompt: str
    session_id: str = ""

sessions = {}

_SMALLTALK_FALLBACK_PROMPT = (
    "How can I help you? Is there anything I can suggest you to plan your trip with?"
)

def _normalize_user_text(text: str) -> str:
    # Keep only letters/numbers/spaces so "hi," -> "hi"
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", (text or "").lower()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned

def _is_greeting_or_farewell(text: str) -> bool:
    t = _normalize_user_text(text)
    if not t:
        return False

    # Single-token greetings/farewells (and common short variants)
    single = {
        "hi",
        "hey",
        "hello",
        "yo",
        "hiya",
        "sup",
        "bye",
        "goodbye",
        "cya",
        "thanks",
        "thank you",
        "thx",
    }
    if t in single:
        return True

    # Short multi-word variants
    multi_prefixes = (
        "good morning",
        "good afternoon",
        "good evening",
        "see you",
        "see ya",
        "talk later",
        "talk to you later",
        "thank you",
    )
    return any(t == p for p in multi_prefixes)

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    """Generates the trip plan using the multi-agent system."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # Handle smalltalk (hi/bye/thanks) without invoking the full pipeline
    if _is_greeting_or_farewell(request.prompt):
        return {"success": True, "data": _SMALLTALK_FALLBACK_PROMPT}
        
    try:
        # Retrieve existing state if session_id is provided
        initial_state = None
        if request.session_id and request.session_id in sessions:
            initial_state = sessions[request.session_id]
            print(f"Main API: Resuming session {request.session_id}")
            
        orchestrator = OrchestratorAgent(initial_state=initial_state)
        # orchestrator.run is async and returns the final itinerary string/json
        itinerary = await orchestrator.run(request.prompt)
        
        # Save state for future conversational turns
        if request.session_id:
            sessions[request.session_id] = orchestrator.state
            
        return {"success": True, "data": itinerary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Receives a voice audio file, sends to Groq Whisper, and returns transcribed text."""
    try:
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            content = await file.read()
            temp_audio.write(content)
            temp_path = temp_audio.name
            
        client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        with open(temp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(temp_path, f.read()),
                model="whisper-large-v3",
                response_format="json",
                language="en",
                temperature=0.0
            )
            
        os.remove(temp_path)
        return {"success": True, "text": transcription.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Use python -m uvicorn main:app --reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
