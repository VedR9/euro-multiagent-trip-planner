import json
import asyncio
from src.state import SharedState, Activity
from src.services.mcp_client import MCPClientManager

class ResearcherAgent:
    def __init__(self, mcp_client: MCPClientManager):
        self.mcp = mcp_client
        
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
                prompt = f"""Extract 3 popular attractions from these search results for {city}.
                Format as a JSON array of objects with keys: name, location (string), estimated_cost (float), duration_hours (float), description.
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
                
                parsed_activities = json.loads(json_str)
                for act in parsed_activities:
                    all_activities.append(Activity(**act))
            except Exception as e:
                print(f"ResearcherAgent: MCP Error on {city}: {e}. Using fallback data.")
                all_activities.append(Activity(
                    name=f"Popular Attraction in {city}",
                    location=city,
                    estimated_cost=25.0,
                    duration_hours=2.0,
                    description="Fallback data used due to MCP rate limit."
                ))
                
        state.candidate_activities = all_activities
        print(f"ResearcherAgent: Found {len(all_activities)} candidate activities via MCP.")
        return state
