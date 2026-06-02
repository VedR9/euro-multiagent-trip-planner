import os
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from src.state import SharedState
from groq import Groq

class ReviewerAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def execute(self, state: SharedState) -> SharedState:
        print("ReviewerAgent: Validating and drafting itinerary using Groq...")
        
        # Prepare context for the LLM to review
        context = (
            f"Original Prompt: {state.original_prompt}\n"
            f"Budget: ${state.profile.budget if state.profile else 0}\n"
            f"Duration: {state.profile.duration_days if state.profile else 0} days\n"
            f"Constraints: {state.profile.constraints if state.profile else []}\n"
            "Candidate Activities:\n"
            f"{[act.model_dump() for act in state.candidate_activities]}\n"
            "Accommodations:\n"
            f"{[acc.model_dump() for acc in state.accommodations]}\n"
        )
        
        prompt = f"""You are the final Reviewer for a premium European Travel Agency.
Your job is to take the requested profile, the discovered activities, and the booked accommodations, and generate a final structured JSON output.

Profile: {state.profile.model_dump_json() if state.profile else 'None'}
Candidate Activities: {[a.model_dump_json() for a in state.candidate_activities]}
Accommodations: {[a.model_dump_json() for a in state.accommodations]}

OUTPUT INSTRUCTIONS:
You must return ONLY a raw JSON object (do not wrap in markdown code blocks) with EXACTLY two keys:
1. "audio_summary": A punchy, 2-3 sentence conversational summary of the trip. This will be spoken out loud by a text-to-speech engine to the user. It should be exciting and specifically mention Europe.
2. "markdown_itinerary": The full, detailed markdown itinerary. If the total cost exceeds the budget, or if the budget is 0, start the markdown with "### Validation Failed" and explain why. Otherwise, provide a beautiful day-by-day European itinerary.

Example Output:
{{
  "audio_summary": "Get ready for an incredible European adventure! You will be staying in the heart of Paris and enjoying luxury dining, all well within your budget.",
  "markdown_itinerary": "## Paris Itinerary\\n..."
}}
"""
        
        try:
            from google import genai
            import os
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            json_output = response.text.strip()
            if json_output.startswith("```json"): json_output = json_output[7:-3]
            elif json_output.startswith("```"): json_output = json_output[3:-3]
            
            # The output should be a JSON string, which we will just store as the final itinerary for the API to parse
            state.final_itinerary = json_output.strip()
            print(f"ReviewerAgent: Successfully drafted European itinerary/feedback.")
        except Exception as e:
            print(f"ReviewerAgent Error: {e}")
            state.final_itinerary = "Error generating itinerary."
            
        return state
