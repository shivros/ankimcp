"""Simple HTTP MCP server for Anki using only standard library."""

import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any, Dict
import urllib.parse

from .anki_interface import AnkiInterface

logger = logging.getLogger(__name__)


class MCPRequestHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for MCP."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "ankimcp"}).encode())
        
        elif self.path == '/tools':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            tools = [
                {
                    "name": "list_decks",
                    "description": "List all available Anki decks",
                    "inputSchema": {"type": "object", "properties": {}, "required": []}
                },
                {
                    "name": "get_deck_info",
                    "description": "Get detailed information about a specific deck",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "deck_name": {
                                "type": "string",
                                "description": "Name of the deck to get info for"
                            }
                        },
                        "required": ["deck_name"]
                    }
                },
                {
                    "name": "search_notes",
                    "description": "Search for notes using Anki's search syntax",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Anki search query"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 50
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_note",
                    "description": "Get detailed information about a specific note",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "integer",
                                "description": "ID of the note to retrieve"
                            }
                        },
                        "required": ["note_id"]
                    }
                },
                {
                    "name": "get_cards_for_note",
                    "description": "Get all cards associated with a specific note",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "note_id": {
                                "type": "integer",
                                "description": "ID of the note"
                            }
                        },
                        "required": ["note_id"]
                    }
                },
                {
                    "name": "get_review_stats",
                    "description": "Get review statistics for a deck or overall",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "deck_name": {
                                "type": "string",
                                "description": "Name of the deck (optional)"
                            }
                        },
                        "required": []
                    }
                }
            ]
            
            self.wfile.write(json.dumps(tools).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path.startswith('/tools/'):
            tool_name = self.path[7:]  # Remove '/tools/' prefix
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            
            try:
                data = json.loads(body) if body else {}
            except:
                data = {}
            
            # Get the Anki interface from the server
            anki = self.server.anki_interface
            
            try:
                # Execute the tool
                if tool_name == "list_decks":
                    result = asyncio.run(anki.list_decks())
                elif tool_name == "get_deck_info":
                    result = asyncio.run(anki.get_deck_info(data["deck_name"]))
                elif tool_name == "search_notes":
                    result = asyncio.run(anki.search_notes(
                        data["query"],
                        limit=data.get("limit", 50)
                    ))
                elif tool_name == "get_note":
                    result = asyncio.run(anki.get_note(data["note_id"]))
                elif tool_name == "get_cards_for_note":
                    result = asyncio.run(anki.get_cards_for_note(data["note_id"]))
                elif tool_name == "get_review_stats":
                    result = asyncio.run(anki.get_review_stats(data.get("deck_name")))
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Unknown tool: {tool_name}"}).encode())
                    return
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
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
        self.server.anki_interface = self.anki
        
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