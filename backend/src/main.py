import os
import sys
import asyncio
from dotenv import load_dotenv
from src.agents.orchestrator import OrchestratorAgent

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
        
    orchestrator = OrchestratorAgent()
    itinerary = await orchestrator.run(prompt)
    
    print("\n" + "="*50)
    print("FINAL ITINERARY & REVIEWER FEEDBACK")
    print("="*50 + "\n")
    print(itinerary)

if __name__ == "__main__":
    asyncio.run(main())
