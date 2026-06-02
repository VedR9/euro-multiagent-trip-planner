import os
import json
from groq import Groq

class MockDataService:
    def __init__(self):
        # Assumes GROQ_API_KEY is loaded in environment
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def get_attractions(self, city: str, preferences: list) -> list:
        prompt = (
            f"Return 3 popular attractions in {city} that match these preferences: {', '.join(preferences)}. "
            "Respond ONLY with valid JSON. The JSON should be a list of objects with the following keys: "
            "'name' (string), 'location' (string), 'estimated_cost' (float), 'duration_hours' (float), 'description' (string)."
        )
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            return json.loads(content)
        except Exception as e:
            print(f"MockDataService Error (Attractions): {e}")
            return []

    def get_hotels(self, city: str, budget: float) -> list:
        prompt = (
            f"Return 2 hotels in {city} that are suitable for a budget of roughly ${budget}/night. "
            "Respond ONLY with valid JSON. The JSON should be a list of objects with the following keys: "
            "'name' (string), 'neighborhood' (string), 'cost_per_night' (float), 'total_cost' (float), 'description' (string)."
        )
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            return json.loads(content)
        except Exception as e:
            print(f"MockDataService Error (Hotels): {e}")
            return []
