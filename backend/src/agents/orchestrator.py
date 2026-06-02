import os
from src.state import SharedState
from src.agents.profiler import ProfilerAgent
from src.agents.researcher import ResearcherAgent
from src.agents.logistics import LogisticsAgent
from src.agents.reviewer import ReviewerAgent
from src.services.mcp_client import MCPClientManager

class OrchestratorAgent:
    def __init__(self, initial_state: SharedState = None):
        self.state = initial_state if initial_state else SharedState()
        self.mcp = MCPClientManager()
        # Initialize specialist agents here
        self.profiler = ProfilerAgent()
        self.researcher = ResearcherAgent(self.mcp)
        self.logistics = LogisticsAgent(self.mcp)
        self.reviewer = ReviewerAgent()

    async def run(self, prompt: str) -> str:
        self.state.original_prompt = prompt
        self.state.status = "processing"
        
        print(f"Orchestrator received prompt: {prompt}")
        
        # Step 1: Profiling
        self.state = self.profiler.execute(self.state)
        
        # Connect to MCP servers before moving to discovery
        # NOTE: Real implementations should ensure npx is installed and paths are correct
        # This will spin up the brave-search and searchapi MCP servers
        try:
            print("Orchestrator: Spinning up MCP Servers...")
            await self.mcp.connect_to_server(
                "tavily", "npx", ["-y", "tavily-mcp"],
                env={"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", "")}
            )
        except Exception as e:
            print(f"Orchestrator Error starting MCP: {e}")
        
        # Step 2: Discovery (Researcher via Groq + MCP)
        self.state = await self.researcher.execute(self.state)
        
        # Fallback Loop for Logistics & Validation
        max_retries = 3
        for attempt in range(max_retries):
            # Step 3: Logistics (Accommodation via Groq + MCP)
            self.state = await self.logistics.execute(self.state)
            
            # Step 4: Drafting & Validation (Reviewer via Gemini)
            self.state = self.reviewer.execute(self.state)
            
            if "### Validation Failed" not in self.state.final_itinerary:
                break
                
            print(f"Orchestrator: Validation failed on attempt {attempt + 1}. Retrying logistics with adjusted parameters...")
            if self.state.profile:
                # Reduce budget slightly to force cheaper options in next iteration
                self.state.profile.budget *= 0.85
        
        await self.mcp.cleanup()
        self.state.status = "completed"
        return self.state.final_itinerary
