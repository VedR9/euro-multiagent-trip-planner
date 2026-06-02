import json
import os
from groq import Groq
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential
from src.state import SharedState, TravelProfile

class ProfilerAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def execute(self, state: SharedState) -> SharedState:
        print(f"ProfilerAgent: Analyzing request using Groq -> '{state.original_prompt}'")
        
        system_message = """You are the Profiler Agent for a premium European Trip Planner.
Your job is to extract travel parameters from the user's prompt. 
You ONLY plan trips to Europe. If the user asks for a non-European destination, gracefully fall back to a popular European alternative (like Paris or Rome) or assume they meant Europe.
Budgets should be considered in Euros (EUR) or GBP.

Extract the following into a valid JSON object:
- destinations (list of strings): Which European cities do they want to visit?
- budget (float): What is their total budget? (Use 0.0 if not explicitly mentioned)
- duration_days (int): How many days? (Use 1 if not explicitly mentioned)
- preferences (list of strings): e.g., ['food', 'temples', 'history']
- constraints (list of strings): e.g., ['hate crowds', 'wheelchair accessible']

Output ONLY the JSON object. Do not wrap in markdown tags."""
        
        if state.profile:
            system_message += f"\n\nHere is the user's EXISTING trip profile:\n{state.profile.model_dump_json()}\n\nThe user wants to modify their trip based on this new request: '{state.original_prompt}'. Return the full, updated JSON profile."
        
        try:
            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": state.original_prompt}
                ],
                temperature=0.1,
            )
            
            # The model is instructed to return only JSON, but we should strip any potential markdown block wrappers
            json_output = response.choices[0].message.content.strip()
            if json_output.startswith("```json"):
                json_output = json_output[7:]
            if json_output.endswith("```"):
                json_output = json_output[:-3]
                
            parsed_profile = TravelProfile.model_validate_json(json_output.strip())
            state.profile = parsed_profile
            print("ProfilerAgent: Successfully extracted European profile.")
        except ValidationError as e:
            print(f"ProfilerAgent Validation Error: {e}")
            raise e
        except Exception as e:
            print(f"ProfilerAgent Error: {e}")
            raise e
            
        return state
