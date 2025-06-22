"""Run the AnkiMCP client that connects to the running Anki server."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ankimcp.client import main


# For backwards compatibility, keep the mock interface
from ankimcp.anki_interface import AnkiInterface


class MockAnkiInterface(AnkiInterface):
    """Mock Anki interface for testing without Anki."""

    def __init__(self):
        # Don't call super().__init__() since we don't have a collection
        pass

    async def list_decks(self):
        return [
            {"id": 1, "name": "Default", "card_count": 10, "is_filtered": False},
            {"id": 2, "name": "Spanish", "card_count": 50, "is_filtered": False},
        ]

    async def get_deck_info(self, deck_name: str):
        if deck_name == "Default":
            return {
                "id": 1,
                "name": "Default",
                "card_count": 10,
                "new_count": 3,
                "learning_count": 2,
                "review_count": 5,
                "is_filtered": False,
                "config": {},
            }
        raise ValueError(f"Deck not found: {deck_name}")

    async def search_notes(self, query: str, limit: int = 50):
        return [
            {
                "id": 1,
                "model_name": "Basic",
                "fields": {"Front": "Hello", "Back": "Hola"},
                "tags": ["spanish"],
                "card_count": 1,
            }
        ]

    async def get_note(self, note_id: int):
        if note_id == 1:
            return {
                "id": 1,
                "model_name": "Basic",
                "fields": {"Front": "Hello", "Back": "Hola"},
                "tags": ["spanish"],
                "card_count": 1,
            }
        raise ValueError(f"Note not found: {note_id}")

    async def get_cards_for_note(self, note_id: int):
        if note_id == 1:
            return [
                {
                    "id": 1,
                    "note_id": 1,
                    "deck_name": "Spanish",
                    "type": 0,
                    "queue": 0,
                    "due": 0,
                    "interval": 0,
                    "ease_factor": 2500,
                    "reviews": 0,
                    "lapses": 0,
                    "last_review": 0,
                }
            ]
        return []

    async def get_review_stats(self, deck_name: Optional[str] = None):
        return {
            "deck_name": deck_name or "All Decks",
            "total_cards": 60,
            "new_cards": 10,
            "learning_cards": 5,
            "review_cards": 45,
            "mature_cards": 30,
        }


if __name__ == "__main__":
    print("Starting AnkiMCP client...")
    print("This client connects to the Anki MCP server running on localhost:4473")
    print("Make sure Anki is running with the AnkiMCP addon installed.")
    asyncio.run(main())
