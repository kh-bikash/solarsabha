import asyncio, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parents[1] / "mcp_server" / "solar_rules_server.py"

def test_mcp_server_lists_and_calls_tools():
    async def go():
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                names = {t.name for t in (await s.list_tools()).tools}
                assert {"get_rule", "size_system", "check_vendor", "scan_for_injection"} <= names
                res = await s.call_tool("size_system", {"annual_kwh": 60000, "flats": 50})
                assert "36" in res.content[0].text
    asyncio.run(go())
