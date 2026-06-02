import asyncio
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    """Manages connections to multiple MCP servers."""
    def __init__(self):
        self.sessions = {}
        self._exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_id: str, command: str, args: list, env: dict = None):
        """Spawns an MCP server via stdio and initializes a session."""
        server_env = os.environ.copy()
        if env:
            server_env.update(env)
            
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=server_env
        )
        
        # Connect via stdio
        stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
        read, write = stdio_transport
        
        session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        
        self.sessions[server_id] = session
        print(f"MCPClientManager: Successfully connected to {server_id}")
        return session

    async def list_tools(self, server_id: str):
        session = self.sessions.get(server_id)
        if not session:
            raise ValueError(f"No active session for {server_id}")
        response = await session.list_tools()
        return response.tools

    async def call_tool(self, server_id: str, tool_name: str, arguments: dict):
        session = self.sessions.get(server_id)
        if not session:
            raise ValueError(f"No active session for {server_id}")
        result = await session.call_tool(tool_name, arguments)
        return result

    async def cleanup(self):
        await self._exit_stack.aclose()
