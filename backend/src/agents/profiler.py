import json
import os
import re
from groq import Groq
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential
from src.state import SharedState, TravelProfile

_COUNTRY_TO_CITIES = {
    # Keep this intentionally small and high-signal; we can extend as needed.
    "switzerland": ["Zurich", "Lucerne", "Interlaken", "Geneva"],
    "france": ["Paris", "Nice", "Lyon"],
    "italy": ["Rome", "Florence", "Venice"],
    "spain": ["Barcelona", "Madrid", "Seville"],
    "germany": ["Berlin", "Munich", "Hamburg"],
    "austria": ["Vienna", "Salzburg", "Innsbruck"],
    "netherlands": ["Amsterdam", "Rotterdam", "Utrecht"],
}

def _normalize_place(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _expand_countries_to_cities(destinations: list[str]) -> list[str]:
    expanded: list[str] = []
    for d in destinations or []:
        key = _normalize_place(d).lower()
        if key in _COUNTRY_TO_CITIES:
            expanded.extend(_COUNTRY_TO_CITIES[key])
        else:
            expanded.append(_normalize_place(d))
    # de-dupe while preserving order
    seen = set()
    out: list[str] = []
    for d in expanded:
        if not d:
            continue
        k = d.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(d)
    return out

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
- budget (float): What is their total budget? (If they mention tiers: low is below 2000 EUR, mid is 2000-5000 EUR, high is 5000+ EUR. Use 5000.0 if not explicitly mentioned)
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
            # If the model returns countries (e.g., "Switzerland"), expand to major cities
            parsed_profile.destinations = _expand_countries_to_cities(parsed_profile.destinations)
            state.profile = parsed_profile
            print("ProfilerAgent: Successfully extracted European profile.")
        except ValidationError as e:
            print(f"ProfilerAgent Validation Error: {e}")
            raise e
        except Exception as e:
            print(f"ProfilerAgent Error: {e}")
            raise e
            
        return state
