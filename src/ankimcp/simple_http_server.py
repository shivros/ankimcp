"""Simple HTTP MCP server for Anki using only standard library."""

import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from .anki_interface import AnkiInterface
from .tools import get_tool_schemas

logger = logging.getLogger(__name__)


class MCPRequestHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for MCP."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "ok", "service": "ankimcp"}).encode()
            )

        elif self.path == "/tools":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            tools = get_tool_schemas()
            self.wfile.write(json.dumps(tools).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests."""
        if self.path.startswith("/tools/"):
            tool_name = self.path[7:]  # Remove '/tools/' prefix

            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()

            try:
                data = json.loads(body) if body else {}
            except Exception:
                data = {}

            # Get the Anki interface from the server
            anki = getattr(self.server, "anki_interface", None)
            if not anki:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "Server not initialized"}).encode()
                )
                return

            try:
                # Execute the tool
                if tool_name == "list_decks":
                    result = asyncio.run(anki.list_decks())
                elif tool_name == "get_deck_info":
                    result = asyncio.run(anki.get_deck_info(data["deck_name"]))
                elif tool_name == "search_notes":
                    result = asyncio.run(
                        anki.search_notes(data["query"], limit=data.get("limit", 50))
                    )
                elif tool_name == "get_note":
                    result = asyncio.run(anki.get_note(data["note_id"]))
                elif tool_name == "get_cards_for_note":
                    result = asyncio.run(anki.get_cards_for_note(data["note_id"]))
                elif tool_name == "get_review_stats":
                    result = asyncio.run(anki.get_review_stats(data.get("deck_name")))
                elif tool_name == "create_deck":
                    result = asyncio.run(anki.create_deck(data["deck_name"]))
                elif tool_name == "create_note_type":
                    result = asyncio.run(
                        anki.create_note_type(
                            data["name"], data["fields"], data["templates"]
                        )
                    )
                elif tool_name == "create_note":
                    result = asyncio.run(
                        anki.create_note(
                            data["model_name"],
                            data["fields"],
                            data["deck_name"],
                            tags=data.get("tags"),
                        )
                    )
                elif tool_name == "update_note":
                    result = asyncio.run(
                        anki.update_note(
                            data["note_id"],
                            fields=data.get("fields"),
                            tags=data.get("tags"),
                        )
                    )
                elif tool_name == "delete_note":
                    result = asyncio.run(anki.delete_note(data["note_id"]))
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"error": f"Unknown tool: {tool_name}"}).encode()
                    )
                    return

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())

            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to use logger instead of stderr."""
        logger.info(f"{self.address_string()} - {format % args}")


class SimpleHTTPServer:
    """Simple HTTP server for AnkiMCP."""

    def __init__(self, anki: AnkiInterface, host: str = "localhost", port: int = 4473):
        self.anki = anki
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Start the HTTP server in a separate thread."""
        self.server = HTTPServer((self.host, self.port), MCPRequestHandler)
        setattr(self.server, "anki_interface", self.anki)

        self.thread = Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        logger.info(f"AnkiMCP HTTP server started on {self.host}:{self.port}")

    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join()
