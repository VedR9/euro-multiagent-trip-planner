import json
import asyncio
from src.state import SharedState, Activity
from src.services.mcp_client import MCPClientManager
from src.services.mock_data import MockDataService

def _mcp_result_to_text(result) -> str:
    """
    MCP tool results typically return an object with a .content list of items like:
    { type: 'text', text: '...' }. We normalize that into plain text.
    """
    try:
        content = getattr(result, "content", None)
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(getattr(item, "text", "")))
            return "\n".join([p for p in parts if p]).strip()
    except Exception:
        pass
    return str(result)

def _extract_tavily_titles(result) -> list[str]:
    """
    Try to pull result titles directly from Tavily output to avoid LLM parsing
    when rate limits are hit.
    """
    # Best case: tool returned a dict-like payload
    if isinstance(result, dict):
        results = result.get("results") or result.get("data") or result.get("result") or []
        if isinstance(results, list):
            titles = [r.get("title") for r in results if isinstance(r, dict) and r.get("title")]
            return [t.strip() for t in titles if isinstance(t, str) and t.strip()]

    # Next: content text contains JSON
    text = _mcp_result_to_text(result)
    try:
        as_json = json.loads(text)
        if isinstance(as_json, dict):
            results = as_json.get("results") or []
            if isinstance(results, list):
                titles = [r.get("title") for r in results if isinstance(r, dict) and r.get("title")]
                return [t.strip() for t in titles if isinstance(t, str) and t.strip()]
    except Exception:
        pass

    return []

class ResearcherAgent:
    def __init__(self, mcp_client: MCPClientManager):
        self.mcp = mcp_client
        self.mock = MockDataService()
        
    async def execute(self, state: SharedState) -> SharedState:
        print("ResearcherAgent: Finding activities via MCP...")
        if not state.profile or not state.profile.destinations:
            print("ResearcherAgent: No destinations found to research.")
            return state
            
        import os
            
        all_activities = []
        for city in state.profile.destinations:
            print(f"ResearcherAgent: Researching {city} using Tavily MCP...")
            try:
                search_results = await self.mcp.call_tool("tavily", "tavily_search", {
                    "query": f"Top attractions in {city} {', '.join(state.profile.preferences)}"
                })
                print(f"ResearcherAgent: Successfully retrieved live data from MCP.")
                
                # Feed search results to Groq to extract real activities
                from groq import Groq
                import os
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                search_text = _mcp_result_to_text(search_results)
                prompt = f"""Extract 3 popular attractions from these search results for {city}.
Format as a JSON array of objects with keys: name, location (string), estimated_cost (float), duration_hours (float), description.
Rules:
- Use real, specific attraction names (no placeholders like "Popular Attraction").
- location should be a neighborhood/city-area if available, otherwise use the city name.
- estimated_cost should be a realistic EUR ticket price estimate (use 0.0 for free attractions).
- duration_hours should be realistic (e.g. 1.5, 2, 3, 4).
Search Results (raw text): {search_text[:6000]}
Return ONLY the raw JSON array.
                """
                response = client.chat.completions.create(
                    model='llama-3.3-70b-versatile',
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                
                json_str = response.choices[0].message.content.strip()
                if json_str.startswith("```json"): json_str = json_str[7:-3]
                
                parsed_activities = json.loads(json_str)
                for act in parsed_activities:
                    all_activities.append(Activity(**act))
            except Exception as e:
                print(f"ResearcherAgent: MCP Error on {city}: {e}. Using fallback data.")
                try:
                    # If Tavily returned structured results, use titles directly (no LLM needed)
                    titles = _extract_tavily_titles(locals().get("search_results"))
                    if titles:
                        for t in titles[:3]:
                            all_activities.append(Activity(
                                name=t,
                                location=city,
                                estimated_cost=0.0,
                                duration_hours=2.0,
                                description="Suggested from live search results."
                            ))
                        continue

                    fallback = self.mock.get_attractions(city, state.profile.preferences if state.profile else [])
                    for act in fallback[:3]:
                        all_activities.append(Activity(**act))
                except Exception as fallback_err:
                    print(f"ResearcherAgent: Fallback generator error on {city}: {fallback_err}. Using placeholder.")
                    all_activities.append(Activity(
                        name=f"Top attractions in {city}",
                        location=city,
                        estimated_cost=0.0,
                        duration_hours=2.0,
                        description="Unable to fetch live attraction data; please refine preferences or try again."
                    ))
                
        state.candidate_activities = all_activities
        print(f"ResearcherAgent: Found {len(all_activities)} candidate activities via MCP.")
        return state
