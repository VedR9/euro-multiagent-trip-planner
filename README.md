## Euro Multi-Agent Voice Trip Planner 🎙️✈️

An AI-powered **voice + chat** trip planner that orchestrates multiple agents to build a detailed, city-level itinerary for Europe.

`https://euro-multiagent-trip-planner.vercel.app/`

## Overview

This project helps users plan a trip to Europe by:
- recording voice (browser mic),
- transcribing it (Whisper via Groq),
- researching real attractions/hotels (Tavily MCP),
- compiling a polished itinerary + audio summary (Reviewer).

### Key behaviors
- **Greeting handling**: inputs like `hi`, `hello,`, `bye`, `thanks` return:  
  **“How can I help you? Is there anything I can suggest you to plan your trip with?”**
- **Country → city expansion**: if a user says a country like **Switzerland**, the planner expands it to major cities (e.g. **Zurich, Lucerne, Interlaken, Geneva**) so outputs are city-level and not generic.
- **Rate-limit resilience**: if Groq/Gemini rate limits occur, the backend falls back to using **live search titles** and/or a deterministic itinerary so responses stay specific and structured.

Demo video (GitHub attachment):
`https://github.com/user-attachments/assets/3548a49f-907c-449b-85b1-92411e031030`

## ✨ Key Features
- **Voice-first UX**: one-tap mic recording → transcription → itinerary.
- **Multi-agent planning pipeline**:
  - **Profiler**: extracts destinations, duration, budget, preferences.
  - **Researcher**: finds specific attractions using live search.
  - **Logistics**: suggests hotels and basic cost estimates.
  - **Reviewer**: validates and formats the final plan.
- **Smalltalk handling**: `hi`, `hi,`, `bye`, `thanks` →  
  **“How can I help you? Is there anything I can suggest you to plan your trip with?”**
- **Country → city expansion**: e.g. **Switzerland → Zurich, Lucerne, Interlaken, Geneva** (prevents “generic country-only” itineraries).
- **Rate-limit resilience**: if Groq/Gemini rate limits occur, the backend falls back to:
  - using **live search result titles** directly, and/or
  - a deterministic itinerary generator (so you still get structured output).

## ⚙️ Architecture & Data Flow

Full diagram + details: `docs/architecture.md`

High-level flow:
1. **Frontend (`frontend/`)** captures voice, calls backend endpoints.
2. **Backend API (`backend/`)**:
   - `POST /api/transcribe` → Groq Whisper transcription
   - `POST /api/plan` → Orchestrator runs the agent pipeline
3. **Orchestrator** coordinates:
   - Profiler → Researcher → Logistics → Reviewer
4. **Shared State (`SharedState`)** carries the structured trip profile, candidate activities, hotels, and final output.

## Local Setup & Execution

### Prerequisites
- **Node.js**: recommended **20+**
- **Python**: **3.11+**
- API keys:
  - `GROQ_API_KEY`
  - `GEMINI_API_KEY`
  - `TAVILY_API_KEY`

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

More details (frontend-focused): `frontend/README.md`

