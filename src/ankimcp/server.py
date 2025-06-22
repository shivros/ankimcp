"""MCP server for exposing Anki data."""

import logging
from typing import Any, Dict, List, Optional

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool

from .anki_interface import AnkiInterface

logger = logging.getLogger(__name__)

app = Server("ankimcp")

# Initialize Anki interface (will be set up when server starts)
anki: Optional[AnkiInterface] = None


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for interacting with Anki."""
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
                        "description": "Anki search query (e.g., 'deck:MyDeck tag:important')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
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
                    "note_id": {"type": "integer", "description": "ID of the note"}
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
                        "description": "Name of the deck (optional, omit for overall stats)",
                    }
                },
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a tool and return results."""
    if anki is None:
        return [TextContent(type="text", text="Error: Anki interface not initialized")]

    try:
        if name == "list_decks":
            decks = await anki.list_decks()
            return [TextContent(type="text", text=str(decks))]

        elif name == "get_deck_info":
            info = await anki.get_deck_info(arguments["deck_name"])
            return [TextContent(type="text", text=str(info))]

        elif name == "search_notes":
            notes = await anki.search_notes(
                arguments["query"], limit=arguments.get("limit", 50)
            )
            return [TextContent(type="text", text=str(notes))]

        elif name == "get_note":
            note = await anki.get_note(arguments["note_id"])
            return [TextContent(type="text", text=str(note))]

        elif name == "get_cards_for_note":
            cards = await anki.get_cards_for_note(arguments["note_id"])
            return [TextContent(type="text", text=str(cards))]

        elif name == "get_review_stats":
            stats = await anki.get_review_stats(arguments.get("deck_name"))
            return [TextContent(type="text", text=str(stats))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main(anki_interface: AnkiInterface):
    """Run the MCP server."""
    global anki
    anki = anki_interface

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
