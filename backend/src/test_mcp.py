import asyncio
from src.services.mcp_client import MCPClientManager

async def main():
    mcp = MCPClientManager()
    try:
        await mcp.connect_to_server("duckduckgo", "npx", ["-y", "@ericthered926/duckduckgo-mcp-server"])
        tools = await mcp.list_tools("duckduckgo")
        print("DuckDuckGo Tools:", [t.name for t in tools])
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await mcp.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
