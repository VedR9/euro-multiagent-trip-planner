## Euro Multi-Agent Voice Trip Planner

Plan a Europe trip via **voice** (Whisper transcription) or **text**, powered by a **multi-agent backend**:
- **Profiler**: extracts destinations/budget/duration/preferences
- **Researcher**: finds real attractions via live search (Tavily MCP)
- **Logistics**: suggests accommodation options via live search
- **Reviewer**: assembles a final itinerary + audio summary

### Key behaviors
- **Smalltalk handling**: inputs like `hi`, `hi,`, `bye`, `thanks` return:  
  “How can I help you? Is there anything I can suggest you to plan your trip with?”
- **Country → city expansion**: if a user says a country like **Switzerland**, the planner expands it to major cities (e.g. **Zurich, Lucerne, Interlaken, Geneva**) so outputs are city-level and not generic.
- **Rate-limit resilience**: if Groq/Gemini rate limits occur, the backend falls back to using **live search titles** and/or a deterministic itinerary so responses stay specific and structured.

## Getting Started

### Prerequisites
- **Node.js**: recommended **20+** (the repo may warn on older Node versions)
- **Python**: **3.11+** for the backend
- API keys:
  - `GROQ_API_KEY` (LLM + Whisper transcription)
  - `GEMINI_API_KEY` (Reviewer itinerary drafting)
  - `TAVILY_API_KEY` (live search via Tavily MCP)

### Frontend (Next.js)
From `frontend/`:

```bash
npm ci

# Point the UI at your backend (optional if using default localhost:8000)
export NEXT_PUBLIC_API_URL="http://localhost:8000"

npm run dev
```

Open `http://localhost:3000`.

### Backend (FastAPI)
From repo root:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

export GROQ_API_KEY="..."
export GEMINI_API_KEY="..."
export TAVILY_API_KEY="..."

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:
- `POST /api/transcribe`: accepts `audio/webm` and returns transcribed text
- `POST /api/plan`: accepts `{ "prompt": "...", "session_id": "..." }` and returns itinerary JSON (as a string) or a smalltalk message

### Quick sanity checks

```bash
# Greeting/smalltalk
curl -sS -X POST "http://localhost:8000/api/plan" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"hi,","session_id":"test"}'

# Trip request
curl -sS -X POST "http://localhost:8000/api/plan" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Plan a premium 5-day family trip to Switzerland under 3500 euros.","session_id":"test"}'
```

## Deployment

### Frontend on Vercel
- Deploy `frontend/` as a Next.js app.
- Set `NEXT_PUBLIC_API_URL` in Vercel env vars to your Hugging Face backend URL.

### Backend on Hugging Face Spaces
- The backend is containerized and exposes port **7860** (see `backend/Dockerfile`).
- Set `GROQ_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY` as Space secrets.

## Troubleshooting

### “Generic outputs” (e.g. “Popular Attraction in Switzerland”)
This usually means **rate limits** were hit on upstream models, causing fallbacks. The backend now tries to:
- expand countries → cities,
- use **live search result titles** directly when LLM extraction is rate limited,
- fall back to a deterministic reviewer output if Gemini quota is exhausted.

If you still see generic output, check your API quotas and ensure `TAVILY_API_KEY` is set.

