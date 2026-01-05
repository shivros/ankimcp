"""Tool definitions for AnkiMCP."""

from mcp.types import Tool

# Define all available tools in one place
AVAILABLE_TOOLS = [
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
                    "description": "Name of the deck (optional)",
                }
            },
            "required": [],
        },
    ),
    Tool(
        name="list_note_types",
        description="List all available note types (models) with their fields and templates",
        inputSchema={"type": "object", "properties": {}, "required": []},
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
    Tool(
        name="delete_deck",
        description="Delete a deck and all its cards. Cannot delete protected decks.",
        inputSchema={
            "type": "object",
            "properties": {
                "deck_name": {
                    "type": "string",
                    "description": "Name of the deck to delete",
                }
            },
            "required": ["deck_name"],
        },
    ),
    Tool(
        name="update_deck",
        description="Update a deck's properties (name, description). Cannot update protected decks.",
        inputSchema={
            "type": "object",
            "properties": {
                "deck_name": {
                    "type": "string",
                    "description": "Current name of the deck to update",
                },
                "new_name": {
                    "type": "string",
                    "description": "New name for the deck (optional)",
                },
                "description": {
                    "type": "string",
                    "description": "New description for the deck (optional)",
                },
            },
            "required": ["deck_name"],
        },
    ),
]


def get_tool_schemas():
    """Get tool schemas for HTTP responses."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
        }
        for tool in AVAILABLE_TOOLS
    ]
