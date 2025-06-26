#!/usr/bin/env python
"""MCP client that connects to the running Anki server via HTTP."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool

from .tools import AVAILABLE_TOOLS

app = Server("ankimcp-client")

# Global HTTP client
client: Optional[httpx.AsyncClient] = None
BASE_URL = "http://localhost:4473"


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Get tools from the Anki HTTP server."""
    global client

    if not client:
        client = httpx.AsyncClient()

    try:
        # Try to get tools from the running server
        response = await client.get(f"{BASE_URL}/tools")
        response.raise_for_status()
        tools_data = response.json()

        # Convert to Tool objects
        tools = []
        for tool_data in tools_data:
            tools.append(Tool(**tool_data))
        return tools

    except (httpx.ConnectError, httpx.HTTPError):
        # Return all available tools even if server is not running
        # Add a status check tool
        tools = AVAILABLE_TOOLS.copy()
        tools.append(
            Tool(
                name="anki_status",
                description="Check if Anki server is running",
                inputSchema={"type": "object", "properties": {}, "required": []},
            )
        )
        return tools


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute tool by calling the Anki HTTP server."""
    global client

    if not client:
        client = httpx.AsyncClient()

    # Special tool to check server status
    if name == "anki_status":
        try:
            response = await client.get(f"{BASE_URL}/health")
            response.raise_for_status()
            return [TextContent(type="text", text="✓ Anki MCP server is running")]
        except Exception:
            return [
                TextContent(
                    type="text",
                    text="✗ Anki MCP server is not running. Please ensure Anki is open and the AnkiMCP addon is installed.",
                )
            ]

    try:
        # Call the tool on the server
        response = await client.post(f"{BASE_URL}/tools/{name}", json=arguments)
        response.raise_for_status()
        result = response.json()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except httpx.ConnectError:
        return [
            TextContent(
                type="text",
                text="Error: Cannot connect to Anki. Please ensure:\n"
                "1. Anki is running\n"
                "2. AnkiMCP addon is installed\n"
                "3. You have opened your profile",
            )
        ]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]
        else:
            error_data = e.response.json()
            return [
                TextContent(
                    type="text", text=f"Error: {error_data.get('error', str(e))}"
                )
            ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP client."""
    global client

    try:
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ankimcp",
                    server_version="0.1.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        if client:
            await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
