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
            name="get_permissions",
            description="Get current permission settings and status",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
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
                            "required": ["name", "qfmt", "afmt"],
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


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a tool and return results."""
    if anki is None:
        return [TextContent(type="text", text="Error: Anki interface not initialized")]

    try:
        if name == "get_permissions":
            permissions = anki.permissions.get_permission_summary()
            return [TextContent(type="text", text=str(permissions))]

        elif name == "list_decks":
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

        elif name == "create_deck":
            result = await anki.create_deck(arguments["deck_name"])
            return [TextContent(type="text", text=str(result))]

        elif name == "create_note_type":
            result = await anki.create_note_type(
                arguments["name"], arguments["fields"], arguments["templates"]
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "create_note":
            result = await anki.create_note(
                arguments["model_name"],
                arguments["fields"],
                arguments["deck_name"],
                arguments.get("tags"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "update_note":
            result = await anki.update_note(
                arguments["note_id"],
                arguments.get("fields"),
                arguments.get("tags"),
            )
            return [TextContent(type="text", text=str(result))]

        elif name == "delete_note":
            result = await anki.delete_note(arguments["note_id"])
            return [TextContent(type="text", text=str(result))]

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
