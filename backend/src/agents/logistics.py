import json
from src.state import SharedState, Accommodation
from src.services.mcp_client import MCPClientManager

class LogisticsAgent:
    def __init__(self, mcp_client: MCPClientManager):
        self.mcp = mcp_client
        
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
                prompt = f"""Extract 1 recommended hotel from these search results for {city}.
                Format as a JSON array containing exactly 1 object with keys: name, neighborhood (string), cost_per_night (float), total_cost (float, multiply cost_per_night by {days}), description.
                Search Results: {str(search_results)[:2000]}
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
                all_hotels.append(Accommodation(
                    name=f"Standard Hotel in {city}",
                    neighborhood="City Center",
                    cost_per_night=hotel_budget * 0.9,
                    total_cost=(hotel_budget * 0.9) * days,
                    description="Fallback data used due to MCP failure."
                ))
                    
        state.accommodations = all_hotels
        print(f"LogisticsAgent: Found {len(all_hotels)} candidate accommodations via MCP.")
        return state
