import os
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from src.state import SharedState
from groq import Groq
from datetime import date

class ReviewerAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def _deterministic_fallback(self, state: SharedState) -> str:
        profile = state.profile
        destinations = profile.destinations if profile else []
        days = profile.duration_days if profile else 0
        budget = profile.budget if profile else 0.0

        activities = state.candidate_activities or []
        hotels = state.accommodations or []

        # Simple cost estimate from our structured data
        activity_cost = sum(float(a.estimated_cost or 0.0) for a in activities)
        hotel_cost = sum(float(h.total_cost or 0.0) for h in hotels)
        total_cost = activity_cost + hotel_cost

        lines: list[str] = []
        lines.append("# Your AI-Crafted Itinerary")
        lines.append("")
        lines.append(f"## Trip Overview ({date.today().isoformat()})")
        lines.append(f"- **Destinations**: {', '.join(destinations) if destinations else 'Europe'}")
        lines.append(f"- **Duration**: {days} days" if days else "- **Duration**: (unspecified)")
        lines.append(f"- **Budget**: €{budget:.2f}")
        lines.append(f"- **Estimated costs (activities + accommodation only)**: €{total_cost:.2f}")
        lines.append("")

        if hotels:
            lines.append("## Accommodation")
            for h in hotels:
                lines.append(f"- **{h.name}** ({h.neighborhood}) — ~€{h.cost_per_night:.0f}/night, ~€{h.total_cost:.0f} total")
            lines.append("")

        if activities:
            lines.append("## Top Attractions (suggested)")
            for a in activities[:12]:
                cost = f"€{a.estimated_cost:.0f}" if (a.estimated_cost is not None) else "€0"
                lines.append(f"- **{a.name}** ({a.location}) — {cost}, ~{a.duration_hours}h")
            lines.append("")

        # Day-by-day: allocate activities evenly across days
        if days and days > 0:
            lines.append("## Day-by-Day Plan")
            per_day = max(1, len(activities) // days) if activities else 0
            idx = 0
            for d in range(1, days + 1):
                lines.append(f"### Day {d}")
                if idx < len(activities):
                    day_acts = activities[idx: idx + per_day]
                    idx += per_day
                    for a in day_acts:
                        lines.append(f"- Visit **{a.name}**")
                else:
                    lines.append("- Flexible day: explore neighborhoods, cafés, and parks at your own pace.")
                lines.append("")

        audio = (
            f"Your {days}-day Swiss-style European trip is ready! "
            f"You’ll visit {', '.join(destinations[:3])}{' and more' if len(destinations) > 3 else ''} with hand-picked sights. "
            f"Want me to optimize it by pace, kids-friendly stops, or food preferences?"
        )
        return json.dumps({"audio_summary": audio, "markdown_itinerary": "\n".join(lines)})

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
2. "markdown_itinerary": The full, detailed markdown itinerary. If the total cost explicitly exceeds the budget, start the markdown with "### Validation Failed" and explain why. Otherwise, provide a beautiful day-by-day European itinerary.

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
            # Fallback: produce a structured itinerary from known data so we don't return generic placeholders
            state.final_itinerary = self._deterministic_fallback(state)
            
        return state
