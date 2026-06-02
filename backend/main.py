from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
from dotenv import load_dotenv
from src.agents.orchestrator import OrchestratorAgent
import groq

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

@app.post("/api/plan")
async def create_plan(request: PlanRequest):
    """Generates the trip plan using the multi-agent system."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
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
