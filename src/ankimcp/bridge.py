"""Bridge to connect Claude Code to the running Anki MCP server."""

import asyncio
import json
from typing import Any, Dict

import httpx
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool


class AnkiMCPBridge:
    """Bridge between Claude's stdio MCP and Anki's HTTP MCP server."""

    def __init__(self, host: str = "localhost", port: int = 4473):
        self.base_url = f"http://{host}:{port}"
        self.client = httpx.AsyncClient()
        self.app = Server("ankimcp-bridge")

        # Register handlers
        self.app.list_tools()(self.list_tools)
        self.app.call_tool()(self.call_tool)

    async def list_tools(self) -> "list[Tool]":
        """Forward tool listing request to Anki server."""
        try:
            response = await self.client.get(f"{self.base_url}/tools")
            response.raise_for_status()
            tools_data = response.json()

            # Convert to Tool objects
            tools = []
            for tool_data in tools_data:
                tools.append(Tool(**tool_data))
            return tools
        except Exception:
            # Fallback to hardcoded tools if server is not running
            return [
                Tool(
                    name="list_decks",
                    description="List all available Anki decks",
                    inputSchema={"type": "object", "properties": {}, "required": []},
                ),
                Tool(
                    name="get_deck_info",
                    description="Get detailed information about a specific deck",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "deck_name": {
                                "type": "string",
                                "description": "Name of the deck to get info for",
                            }
                        },
                        "required": ["deck_name"],
                    },
                ),
                Tool(
                    name="search_notes",
                    description="Search for notes using Anki's search syntax",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Anki search query",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 50,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="get_note",
                    description="Get detailed information about a specific note",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "integer",
                                "description": "ID of the note to retrieve",
                            }
                        },
                        "required": ["note_id"],
                    },
                ),
                Tool(
                    name="get_cards_for_note",
                    description="Get all cards associated with a specific note",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "integer",
                                "description": "ID of the note",
                            }
                        },
                        "required": ["note_id"],
                    },
                ),
                Tool(
                    name="get_review_stats",
                    description="Get review statistics for a deck or overall",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "deck_name": {
                                "type": "string",
                                "description": "Name of the deck (optional)",
                            }
                        },
                        "required": [],
                    },
                ),
                Tool(
                    name="create_deck",
                    description="Create a new deck",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "deck_name": {
                                "type": "string",
                                "description": "Name of the deck to create",
                            }
                        },
                        "required": ["deck_name"],
                    },
                ),
                Tool(
                    name="create_note_type",
                    description="Create a new note type (model)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the note type",
                            },
                            "fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of field names",
                            },
                            "templates": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "qfmt": {"type": "string"},
                                        "afmt": {"type": "string"},
                                    },
                                },
                                "description": "List of card templates",
                            },
                        },
                        "required": ["name", "fields", "templates"],
                    },
                ),
                Tool(
                    name="create_note",
                    description="Create a new note",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_name": {
                                "type": "string",
                                "description": "Name of the note type (model)",
                            },
                            "fields": {
                                "type": "object",
                                "description": "Field name to value mapping",
                            },
                            "deck_name": {
                                "type": "string",
                                "description": "Name of the deck to add the note to",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional list of tags",
                            },
                        },
                        "required": ["model_name", "fields", "deck_name"],
                    },
                ),
                Tool(
                    name="update_note",
                    description="Update an existing note",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "integer",
                                "description": "ID of the note to update",
                            },
                            "fields": {
                                "type": "object",
                                "description": "Field name to value mapping (only fields to update)",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "New list of tags (replaces existing tags)",
                            },
                        },
                        "required": ["note_id"],
                    },
                ),
                Tool(
                    name="delete_note",
                    description="Delete a note and all its cards",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "integer",
                                "description": "ID of the note to delete",
                            }
                        },
                        "required": ["note_id"],
                    },
                ),
            ]

    async def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> "list[TextContent]":
        """Forward tool execution to Anki server."""
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/{name}", json=arguments
            )
            response.raise_for_status()
            result = response.json()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except httpx.ConnectError:
            return [
                TextContent(
                    type="text",
                    text="Error: Cannot connect to Anki MCP server. Make sure Anki is running.",
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def run(self):
        """Run the bridge server."""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ankimcp-bridge",
                    server_version="0.1.0",
                    capabilities=self.app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


async def main():
    """Run the bridge."""
    bridge = AnkiMCPBridge()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
