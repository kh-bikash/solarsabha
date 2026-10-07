"""Connect agents to the SolarRules MCP server. Use as a context manager:

    with solar_rules_mcp() as tools:
        secretary = build_secretary(extra_tools=tools)
"""
import sys
from contextlib import contextmanager
from pathlib import Path
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient

SERVER = Path(__file__).resolve().parents[2] / "mcp_server" / "solar_rules_server.py"

@contextmanager
def solar_rules_mcp():
    client = MCPClient(lambda: stdio_client(StdioServerParameters(command=sys.executable, args=[str(SERVER)])))
    with client:
        yield client.list_tools_sync()
