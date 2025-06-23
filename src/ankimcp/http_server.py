"""HTTP MCP server for Anki that can be accessed by a bridge."""

import logging

from aiohttp import web

from .anki_interface import AnkiInterface

logger = logging.getLogger(__name__)


class AnkiMCPHTTPServer:
    """HTTP server that exposes Anki data via MCP-compatible endpoints."""

    def __init__(self, anki: AnkiInterface, host: str = "localhost", port: int = 4473):
        self.anki = anki
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Set up HTTP routes."""
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/tools", self.list_tools)
        self.app.router.add_post("/tools/{tool_name}", self.call_tool)

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "ok", "service": "ankimcp"})

    async def list_tools(self, request: web.Request) -> web.Response:
        """List available tools."""
        tools = [
            {
                "name": "list_decks",
                "description": "List all available Anki decks",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_deck_info",
                "description": "Get detailed information about a specific deck",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "deck_name": {
                            "type": "string",
                            "description": "Name of the deck to get info for",
                        }
                    },
                    "required": ["deck_name"],
                },
            },
            {
                "name": "search_notes",
                "description": "Search for notes using Anki's search syntax",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Anki search query"},
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 50,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_note",
                "description": "Get detailed information about a specific note",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "note_id": {
                            "type": "integer",
                            "description": "ID of the note to retrieve",
                        }
                    },
                    "required": ["note_id"],
                },
            },
            {
                "name": "get_cards_for_note",
                "description": "Get all cards associated with a specific note",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "note_id": {"type": "integer", "description": "ID of the note"}
                    },
                    "required": ["note_id"],
                },
            },
            {
                "name": "get_review_stats",
                "description": "Get review statistics for a deck or overall",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "deck_name": {
                            "type": "string",
                            "description": "Name of the deck (optional)",
                        }
                    },
                    "required": [],
                },
            },
        ]
        return web.json_response(tools)

    async def call_tool(self, request: web.Request) -> web.Response:
        """Execute a tool and return results."""
        tool_name = request.match_info["tool_name"]

        try:
            data = await request.json()
        except Exception:
            data = {}

        try:
            if tool_name == "list_decks":
                result = await self.anki.list_decks()
            elif tool_name == "get_deck_info":
                result = await self.anki.get_deck_info(data["deck_name"])
            elif tool_name == "search_notes":
                result = await self.anki.search_notes(
                    data["query"], limit=data.get("limit", 50)
                )
            elif tool_name == "get_note":
                result = await self.anki.get_note(data["note_id"])
            elif tool_name == "get_cards_for_note":
                result = await self.anki.get_cards_for_note(data["note_id"])
            elif tool_name == "get_review_stats":
                result = await self.anki.get_review_stats(data.get("deck_name"))
            else:
                return web.json_response(
                    {"error": f"Unknown tool: {tool_name}"}, status=404
                )

            return web.json_response(result)

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def start(self):
        """Start the HTTP server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"AnkiMCP HTTP server started on {self.host}:{self.port}")
        return runner
