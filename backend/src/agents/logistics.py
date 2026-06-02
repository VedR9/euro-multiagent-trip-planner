import json
from src.state import SharedState, Accommodation
from src.services.mcp_client import MCPClientManager
from src.services.mock_data import MockDataService

def _mcp_result_to_text(result) -> str:
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
    if isinstance(result, dict):
        results = result.get("results") or result.get("data") or result.get("result") or []
        if isinstance(results, list):
            titles = [r.get("title") for r in results if isinstance(r, dict) and r.get("title")]
            return [t.strip() for t in titles if isinstance(t, str) and t.strip()]
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

class LogisticsAgent:
    def __init__(self, mcp_client: MCPClientManager):
        self.mcp = mcp_client
        self.mock = MockDataService()
        
    async def execute(self, state: SharedState) -> SharedState:
        print("LogisticsAgent: Finding accommodations via MCP...")
        if not state.profile or not state.profile.destinations:
            print("LogisticsAgent: No destinations found.")
            return state
            
        days = state.profile.duration_days if state.profile.duration_days > 0 else 1
        daily_budget = state.profile.budget / days if state.profile.budget > 0 else 100.0
        hotel_budget = daily_budget * 0.5
            
        all_hotels = []
        for city in state.profile.destinations:
            print(f"LogisticsAgent: Researching hotels for {city} using Tavily MCP...")
            try:
                search_results = await self.mcp.call_tool("tavily", "tavily_search", {
                    "query": f"Best hotels in {city}"
                })
                
                print(f"LogisticsAgent: Successfully retrieved live hotel data from MCP.")
                
                from groq import Groq
                import os
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                search_text = _mcp_result_to_text(search_results)
                prompt = f"""Extract 1 recommended hotel from these search results for {city}.
Format as a JSON array containing exactly 1 object with keys: name, neighborhood (string), cost_per_night (float), total_cost (float, multiply cost_per_night by {days}), description.
Rules:
- Use a real hotel name (no placeholders like "Standard Hotel").
- cost_per_night must be a realistic EUR estimate and total_cost must equal cost_per_night * {days}.
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
                
                parsed_hotels = json.loads(json_str)
                for h in parsed_hotels:
                    all_hotels.append(Accommodation(**h))
            except Exception as e:
                print(f"LogisticsAgent: MCP Error on {city}: {e}. Using fallback data.")
                try:
                    # If Tavily returned structured results, use titles directly (no LLM needed)
                    titles = _extract_tavily_titles(locals().get("search_results"))
                    if titles:
                        name = titles[0]
                        all_hotels.append(Accommodation(
                            name=name,
                            neighborhood="Central",
                            cost_per_night=hotel_budget * 0.9,
                            total_cost=(hotel_budget * 0.9) * days,
                            description="Suggested from live search results."
                        ))
                        continue

                    # MockDataService expects per-night budget; use our computed hotel_budget
                    fallback_hotels = self.mock.get_hotels(city, hotel_budget)
                    if fallback_hotels:
                        h = fallback_hotels[0]
                        # Ensure totals align with our trip duration
                        cost_per_night = float(h.get("cost_per_night", hotel_budget * 0.9))
                        all_hotels.append(Accommodation(
                            name=h.get("name", f"Hotel in {city}"),
                            neighborhood=h.get("neighborhood", "City Center"),
                            cost_per_night=cost_per_night,
                            total_cost=cost_per_night * days,
                            description=h.get("description", "Fallback hotel data used due to MCP failure.")
                        ))
                    else:
                        raise ValueError("Empty fallback hotels")
                except Exception as fallback_err:
                    print(f"LogisticsAgent: Fallback generator error on {city}: {fallback_err}. Using placeholder.")
                    all_hotels.append(Accommodation(
                        name=f"Hotel in {city}",
                        neighborhood="City Center",
                        cost_per_night=hotel_budget * 0.9,
                        total_cost=(hotel_budget * 0.9) * days,
                        description="Unable to fetch live hotel data; please try again."
                    ))
                    
        state.accommodations = all_hotels
        print(f"LogisticsAgent: Found {len(all_hotels)} candidate accommodations via MCP.")
        return state
