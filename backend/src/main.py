import os
import sys
import asyncio
from dotenv import load_dotenv
from src.agents.orchestrator import OrchestratorAgent
import re

async def main():
    load_dotenv()
    
    if not os.getenv("GROQ_API_KEY") or not os.getenv("GEMINI_API_KEY"):
        print("Error: Missing one or more required API keys in environment variables (.env).")
        print("Ensure GROQ_API_KEY and GEMINI_API_KEY are set.")
        sys.exit(1)
        
    print("Welcome to the Multi-Agent Travel Planner!")
    prompt = input("Enter your travel request: ")
    
    if not prompt.strip():
        print("Prompt cannot be empty. Exiting.")
        sys.exit(1)

    def _normalize_user_text(text: str) -> str:
        cleaned = re.sub(r"[^a-z0-9\s]+", " ", (text or "").lower()).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    def _is_greeting_or_farewell(text: str) -> bool:
        t = _normalize_user_text(text)
        if not t:
            return False
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
        multi = (
            "good morning",
            "good afternoon",
            "good evening",
            "see you",
            "see ya",
            "talk later",
            "talk to you later",
            "thank you",
        )
        return any(t == p for p in multi)

    if _is_greeting_or_farewell(prompt):
        print("How can I help you? Is there anything I can suggest you to plan your trip with?")
        sys.exit(0)
        
    orchestrator = OrchestratorAgent()
    itinerary = await orchestrator.run(prompt)
    
    print("\n" + "="*50)
    print("FINAL ITINERARY & REVIEWER FEEDBACK")
    print("="*50 + "\n")
    print(itinerary)

if __name__ == "__main__":
    asyncio.run(main())
