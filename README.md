## Euro Multi-Agent Voice Trip Planner

Plan a Europe trip via **voice** (Whisper transcription) or **text**, powered by a **multi-agent backend**.

- **Live demo**: `euro-multiagent-trip-planner.vercel.app` (Vercel)
- **Backend**: `backend/` (FastAPI + multi-agent planner)
- **Frontend**: `frontend/` (Next.js voice + chat UI)

### What makes it “multi-agent”
- **Profiler**: extracts destinations/budget/duration/preferences
- **Researcher**: finds real attractions via live search (Tavily MCP)
- **Logistics**: suggests accommodation options via live search
- **Reviewer**: assembles a final itinerary + audio summary (and validates vs budget)

### Key behaviors
- **Greeting handling**: inputs like `hi`, `hello,`, `bye`, `thanks` return:  
  “How can I help you? Is there anything I can suggest you to plan your trip with?”
- **Country → city expansion**: if a user says a country like **Switzerland**, the planner expands it to major cities (e.g. **Zurich, Lucerne, Interlaken, Geneva**) so outputs are city-level and not generic.
- **Rate-limit resilience**: if Groq/Gemini rate limits occur, the backend falls back to using **live search titles** and/or a deterministic itinerary so responses stay specific and structured.


https://github.com/user-attachments/assets/3548a49f-907c-449b-85b1-92411e031030


## Architecture

See `docs/architecture.md` for the full system design.

At a high level:
- `OrchestratorAgent` coordinates the workflow
- A shared `SharedState` object carries profile + candidate activities + hotels + final output

## Local Setup

### Prerequisites
- **Node.js**: recommended **20+**
- **Python**: **3.11+**
- API keys:
  - `GROQ_API_KEY` (LLM + Whisper transcription)
  - `GEMINI_API_KEY` (Reviewer itinerary drafting)
  - `TAVILY_API_KEY` (live search via Tavily MCP)

### Backend (FastAPI)

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

Endpoints:
- `POST /api/transcribe`
- `POST /api/plan`

### Frontend (Next.js)

```bash
cd frontend
npm ci

export NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Open `http://localhost:3000`.

## Quick sanity checks

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
- Set `NEXT_PUBLIC_API_URL` to your Hugging Face backend URL.

### Backend on Hugging Face Spaces
- Backend exposes port **7860** (see `backend/Dockerfile`).
- Set Space secrets: `GROQ_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`.

## Troubleshooting

### “Generic outputs” (e.g. “Popular Attraction in Switzerland”)
Usually means upstream APIs hit **rate limits**. The backend now tries to:
- expand countries → cities,
- use **live search result titles** directly when LLM extraction is rate limited,
- fall back to a deterministic reviewer output if Gemini quota is exhausted.

If you still see generic output, check quotas and verify `TAVILY_API_KEY` is set.

---

For more details, also see `frontend/README.md`.

