"""MCP-compliant HTTP server for Anki using JSON-RPC 2.0 with SSE transport.

Supports two transport modes:
- POST /mcp: Direct JSON-RPC requests (simple, stateless)
- GET /sse + POST /messages: SSE transport for streaming (MCP standard)

The SSE transport is the standard MCP HTTP transport that LLM clients expect.
"""

import asyncio
import json
import logging
import queue
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock, Thread
from typing import Any, Dict, Optional

from .anki_interface import AnkiInterface
from .tools import AVAILABLE_TOOLS

logger = logging.getLogger(__name__)

# MCP Protocol Constants
PROTOCOL_VERSION = "2025-11-25"
SERVER_INFO = {
    "name": "ankimcp",
    "version": "0.1.0",
}
SERVER_CAPABILITIES = {
    "tools": {"listChanged": False},
    "resources": {"subscribe": False, "listChanged": False},
    "logging": {},
}

# JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class SSESessionManager:
    """Manage SSE sessions for MCP clients."""

    def __init__(self):
        self._sessions: Dict[str, queue.Queue] = {}
        self._lock = Lock()

    def create_session(self) -> str:
        """Create a new SSE session and return its ID."""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._sessions[session_id] = queue.Queue()
        logger.info(f"SSE session created: {session_id}")
        return session_id

    def remove_session(self, session_id: str) -> None:
        """Remove an SSE session."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"SSE session removed: {session_id}")

    def get_queue(self, session_id: str) -> Optional[queue.Queue]:
        """Get the message queue for a session."""
        with self._lock:
            return self._sessions.get(session_id)

    def send_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to an SSE session."""
        q = self.get_queue(session_id)
        if q:
            q.put(message)
            return True
        return False

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        with self._lock:
            return session_id in self._sessions


# Global session manager
sse_sessions = SSESessionManager()


class JSONRPCHandler:
    """Handle JSON-RPC 2.0 message parsing and formatting."""

    @staticmethod
    def parse_request(body: str) -> Dict[str, Any]:
        """Parse a JSON-RPC request from the body string."""
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            raise JSONRPCError(PARSE_ERROR, f"Parse error: {e}")

        if not isinstance(data, dict):
            raise JSONRPCError(INVALID_REQUEST, "Request must be an object")

        if data.get("jsonrpc") != "2.0":
            raise JSONRPCError(INVALID_REQUEST, "Must be JSON-RPC 2.0")

        if "method" not in data:
            raise JSONRPCError(INVALID_REQUEST, "Missing 'method' field")

        return data

    @staticmethod
    def success_response(request_id: Any, result: Any) -> Dict[str, Any]:
        """Create a successful JSON-RPC response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    @staticmethod
    def error_response(
        request_id: Any, code: int, message: str, data: Any = None
    ) -> Dict[str, Any]:
        """Create an error JSON-RPC response."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error,
        }


class JSONRPCError(Exception):
    """Exception for JSON-RPC errors."""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class MCPRequestHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for MCP JSON-RPC with SSE support."""

    # Increase timeout for SSE connections
    timeout = 300  # 5 minutes

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._send_json_response(200, {"status": "ok", "service": "ankimcp"})
        elif self.path == "/sse":
            self._handle_sse()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests - MCP JSON-RPC endpoint."""
        if self.path == "/mcp":
            self._handle_mcp_post()
        elif self.path.startswith("/messages"):
            self._handle_messages_post()
        else:
            self.send_error(404, "Not Found")

    def _handle_sse(self):
        """Handle SSE connection for MCP transport."""
        # Create a new session
        session_id = sse_sessions.create_session()

        try:
            # Send SSE headers
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            # Send the endpoint event telling client where to POST messages
            endpoint_event = (
                f"event: endpoint\ndata: /messages?session_id={session_id}\n\n"
            )
            self.wfile.write(endpoint_event.encode("utf-8"))
            self.wfile.flush()

            logger.info(f"SSE client connected, session: {session_id}")

            # Keep connection open and send messages from queue
            msg_queue = sse_sessions.get_queue(session_id)
            while msg_queue is not None:
                try:
                    # Wait for messages with timeout to check if connection is alive
                    message = msg_queue.get(timeout=30)

                    # Send the message as SSE event
                    data = json.dumps(message)
                    sse_event = f"event: message\ndata: {data}\n\n"
                    self.wfile.write(sse_event.encode("utf-8"))
                    self.wfile.flush()

                except queue.Empty:
                    # Send keep-alive comment
                    try:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break
                except (BrokenPipeError, ConnectionResetError):
                    break

                # Check if session still exists
                msg_queue = sse_sessions.get_queue(session_id)

        except Exception as e:
            logger.error(f"SSE error: {e}")
        finally:
            sse_sessions.remove_session(session_id)
            logger.info(f"SSE client disconnected, session: {session_id}")

    def _handle_messages_post(self):
        """Handle POST messages from SSE clients."""
        # Extract session_id from query string
        session_id = None
        if "?" in self.path:
            query = self.path.split("?", 1)[1]
            for param in query.split("&"):
                if param.startswith("session_id="):
                    session_id = param.split("=", 1)[1]
                    break

        if not session_id or not sse_sessions.session_exists(session_id):
            self._send_json_response(
                400,
                JSONRPCHandler.error_response(
                    None, INVALID_REQUEST, "Invalid or missing session_id"
                ),
            )
            return

        # Read and process the message
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        request_id = None
        try:
            request = JSONRPCHandler.parse_request(body)
            request_id = request.get("id")
            method = request["method"]
            params = request.get("params", {})

            # Process the request
            result = self._handle_method(method, params)

            # Send response via SSE
            response = JSONRPCHandler.success_response(request_id, result)
            sse_sessions.send_message(session_id, response)

            # Also send HTTP 202 Accepted
            self.send_response(202)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "accepted"}')

        except JSONRPCError as e:
            response = JSONRPCHandler.error_response(
                request_id, e.code, e.message, e.data
            )
            sse_sessions.send_message(session_id, response)
            self.send_response(202)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "accepted"}')
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            response = JSONRPCHandler.error_response(
                request_id, INTERNAL_ERROR, f"Internal error: {str(e)}"
            )
            sse_sessions.send_message(session_id, response)
            self.send_response(202)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "accepted"}')

    def _handle_mcp_post(self):
        """Handle direct POST to /mcp (stateless JSON-RPC)."""
        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        request_id = None
        try:
            # Parse JSON-RPC request
            request = JSONRPCHandler.parse_request(body)
            request_id = request.get("id")
            method = request["method"]
            params = request.get("params", {})

            # Route to appropriate handler
            result = self._handle_method(method, params)

            # Send success response
            response = JSONRPCHandler.success_response(request_id, result)
            self._send_json_response(200, response)

        except JSONRPCError as e:
            response = JSONRPCHandler.error_response(
                request_id, e.code, e.message, e.data
            )
            self._send_json_response(200, response)
        except Exception as e:
            logger.error(f"Internal error handling request: {e}")
            response = JSONRPCHandler.error_response(
                request_id, INTERNAL_ERROR, f"Internal error: {str(e)}"
            )
            self._send_json_response(200, response)

    def _handle_method(self, method: str, params: Dict[str, Any]) -> Any:
        """Route method to appropriate handler."""
        handlers = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "logging/setLevel": self._handle_logging_set_level,
        }

        handler = handlers.get(method)
        if handler is None:
            raise JSONRPCError(METHOD_NOT_FOUND, f"Method not found: {method}")

        return handler(params)

    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        client_info = params.get("clientInfo", {})
        logger.info(f"MCP client connected: {client_info.get('name', 'unknown')}")

        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": SERVER_CAPABILITIES,
        }

    def _handle_initialized(self, params: Dict[str, Any]) -> None:
        """Handle initialized notification."""
        logger.info("MCP client initialization complete")
        return None

    def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request."""
        return {}

    def _handle_logging_set_level(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle logging/setLevel request.

        Allows clients to control the server's logging verbosity.
        Valid levels: debug, info, notice, warning, error, critical, alert, emergency
        """
        level = params.get("level")
        if not level:
            raise JSONRPCError(INVALID_PARAMS, "Missing 'level' parameter")

        # Map MCP log levels to Python logging levels
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "notice": logging.INFO,  # Python doesn't have NOTICE, map to INFO
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
            "alert": logging.CRITICAL,  # Python doesn't have ALERT, map to CRITICAL
            "emergency": logging.CRITICAL,  # Python doesn't have EMERGENCY
        }

        python_level = level_map.get(level.lower())
        if python_level is None:
            raise JSONRPCError(
                INVALID_PARAMS,
                f"Invalid log level: {level}. Valid levels: {', '.join(level_map.keys())}",
            )

        # Set the log level for the ankimcp logger
        logging.getLogger("ankimcp").setLevel(python_level)
        logger.info(f"Log level set to: {level}")

        return {}

    def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in AVAILABLE_TOOLS
        ]
        return {"tools": tools}

    def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request.

        Returns decks and note types as browsable resources.
        URI scheme:
        - anki://deck/{deck_name} - A deck containing notes
        - anki://note/{note_id} - A specific note
        """
        anki: Optional[AnkiInterface] = getattr(self.server, "anki_interface", None)
        if not anki:
            raise JSONRPCError(INTERNAL_ERROR, "Anki interface not initialized")

        resources = []

        # Add decks as resources
        decks = asyncio.run(anki.list_decks())
        for deck in decks:
            deck_name = deck["name"]
            # URL-encode the deck name for the URI
            encoded_name = deck_name.replace(" ", "%20")
            resources.append(
                {
                    "uri": f"anki://deck/{encoded_name}",
                    "name": deck_name,
                    "description": f"Anki deck with {deck['card_count']} cards",
                    "mimeType": "application/json",
                }
            )

        return {"resources": resources}

    def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request.

        Reads content from:
        - anki://deck/{deck_name} - Returns notes in the deck
        - anki://note/{note_id} - Returns note details
        """
        uri = params.get("uri")
        if not uri:
            raise JSONRPCError(INVALID_PARAMS, "Missing 'uri' parameter")

        anki: Optional[AnkiInterface] = getattr(self.server, "anki_interface", None)
        if not anki:
            raise JSONRPCError(INTERNAL_ERROR, "Anki interface not initialized")

        # Parse the URI
        if not uri.startswith("anki://"):
            raise JSONRPCError(INVALID_PARAMS, f"Invalid URI scheme: {uri}")

        path = uri[7:]  # Remove "anki://"

        if path.startswith("deck/"):
            # Read deck contents (list of notes)
            deck_name = path[5:].replace("%20", " ")  # URL decode
            return self._read_deck_resource(anki, deck_name, uri)
        elif path.startswith("note/"):
            # Read note details
            try:
                note_id = int(path[5:])
            except ValueError:
                raise JSONRPCError(INVALID_PARAMS, f"Invalid note ID: {path[5:]}")
            return self._read_note_resource(anki, note_id, uri)
        else:
            raise JSONRPCError(INVALID_PARAMS, f"Unknown resource path: {path}")

    def _read_deck_resource(
        self, anki: AnkiInterface, deck_name: str, uri: str
    ) -> Dict[str, Any]:
        """Read a deck resource - returns notes in the deck."""
        # Search for notes in this deck
        notes = asyncio.run(anki.search_notes(f'"deck:{deck_name}"', limit=100))

        content = {
            "deck_name": deck_name,
            "note_count": len(notes),
            "notes": notes,
        }

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(content, indent=2),
                }
            ]
        }

    def _read_note_resource(
        self, anki: AnkiInterface, note_id: int, uri: str
    ) -> Dict[str, Any]:
        """Read a note resource - returns note details."""
        note = asyncio.run(anki.get_note(note_id))
        cards = asyncio.run(anki.get_cards_for_note(note_id))

        content = {
            **note,
            "cards": cards,
        }

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(content, indent=2),
                }
            ]
        }

    def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise JSONRPCError(INVALID_PARAMS, "Missing 'name' parameter")

        # Get the Anki interface from the server
        anki: Optional[AnkiInterface] = getattr(self.server, "anki_interface", None)
        if not anki:
            raise JSONRPCError(INTERNAL_ERROR, "Anki interface not initialized")

        try:
            result = self._execute_tool(anki, tool_name, arguments)
            return {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                "isError": False,
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            }

    def _execute_tool(
        self, anki: AnkiInterface, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Execute a tool and return the result."""
        tool_handlers = {
            "get_permissions": lambda: anki.permissions.get_permission_summary(),
            "list_decks": lambda: asyncio.run(anki.list_decks()),
            "get_deck_info": lambda: asyncio.run(
                anki.get_deck_info(arguments["deck_name"])
            ),
            "search_notes": lambda: asyncio.run(
                anki.search_notes(arguments["query"], limit=arguments.get("limit", 50))
            ),
            "get_note": lambda: asyncio.run(anki.get_note(arguments["note_id"])),
            "get_cards_for_note": lambda: asyncio.run(
                anki.get_cards_for_note(arguments["note_id"])
            ),
            "get_review_stats": lambda: asyncio.run(
                anki.get_review_stats(arguments.get("deck_name"))
            ),
            "list_note_types": lambda: asyncio.run(anki.list_note_types()),
            "create_deck": lambda: asyncio.run(
                anki.create_deck(arguments["deck_name"])
            ),
            "create_note_type": lambda: asyncio.run(
                anki.create_note_type(
                    arguments["name"], arguments["fields"], arguments["templates"]
                )
            ),
            "create_note": lambda: asyncio.run(
                anki.create_note(
                    arguments["model_name"],
                    arguments["fields"],
                    arguments["deck_name"],
                    tags=arguments.get("tags"),
                )
            ),
            "update_note": lambda: asyncio.run(
                anki.update_note(
                    arguments["note_id"],
                    fields=arguments.get("fields"),
                    tags=arguments.get("tags"),
                )
            ),
            "delete_note": lambda: asyncio.run(anki.delete_note(arguments["note_id"])),
            "delete_deck": lambda: asyncio.run(
                anki.delete_deck(arguments["deck_name"])
            ),
            "update_deck": lambda: asyncio.run(
                anki.update_deck(
                    arguments["deck_name"],
                    arguments.get("new_name"),
                    arguments.get("description"),
                )
            ),
        }

        handler = tool_handlers.get(tool_name)
        if handler is None:
            raise JSONRPCError(INVALID_PARAMS, f"Unknown tool: {tool_name}")

        return handler()

    def _send_json_response(self, status_code: int, data: Any) -> None:
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        """Override to use logger instead of stderr."""
        logger.debug(f"{self.address_string()} - {format % args}")


class ThreadedHTTPServer(HTTPServer):
    """HTTPServer that handles each request in a new thread (for SSE support)."""

    daemon_threads = True
    allow_reuse_address = True

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        thread = Thread(
            target=self.process_request_thread, args=(request, client_address)
        )
        thread.daemon = self.daemon_threads
        thread.start()

    def process_request_thread(self, request, client_address):
        """Process request in thread."""
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


class SimpleHTTPServer:
    """MCP-compliant HTTP server for AnkiMCP with SSE support."""

    def __init__(self, anki: AnkiInterface, host: str = "localhost", port: int = 4473):
        self.anki = anki
        self.host = host
        self.port = port
        self.server: Optional[ThreadedHTTPServer] = None
        self.thread: Optional[Thread] = None

    def start(self) -> None:
        """Start the HTTP server in a separate thread."""
        self.server = ThreadedHTTPServer((self.host, self.port), MCPRequestHandler)
        setattr(self.server, "anki_interface", self.anki)

        self.thread = Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        base_url = f"http://{self.host}:{self.port}"
        logger.info("AnkiMCP server started:")
        logger.info(f"  SSE endpoint: {base_url}/sse")
        logger.info(f"  Messages endpoint: {base_url}/messages")
        logger.info(f"  Direct JSON-RPC: {base_url}/mcp")
        logger.info(f"  Health check: {base_url}/health")

    def stop(self) -> None:
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join()
            logger.info("AnkiMCP server stopped")
