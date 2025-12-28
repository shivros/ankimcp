"""Standalone MCP bridge with in-memory mock Anki data.

This module runs the existing MCP server against a realistic mock Anki
interface so the client can be exercised without a live Anki process.
"""

import asyncio
import logging
import os
from copy import deepcopy
from typing import Dict, List, Optional

from .anki_interface import AnkiInterface
from .permissions import PermissionAction, PermissionError, PermissionManager
from .server import main as server_main
from .tools import AVAILABLE_TOOLS

logger = logging.getLogger(__name__)

# Static permission config with a mix of allowed and intentionally restricted paths
DEFAULT_PERMISSION_CONFIG = {
    "permissions": {
        "global": {"read": True, "write": True, "delete": True},
        "mode": "allowlist",
        "deck_permissions": {
            "allowlist": ["Default", "Languages::*", "Personal::*"],
            "denylist": ["Archive::*"],
        },
        "protected_decks": ["Languages::Core"],
        "tag_restrictions": {
            "protected_tags": ["locked", "teacher"],
            "readonly_tags": ["archived", "shared"],
        },
        "note_type_permissions": {
            "allow_create": True,
            "allow_modify": True,
            "allowed_types": [],
        },
    }
}


class BridgeAnkiInterface(AnkiInterface):
    """Mock Anki interface used by the standalone bridge server."""

    def __init__(self):
        # Do not call super().__init__ since we are not running inside Anki
        self.permissions = PermissionManager(DEFAULT_PERMISSION_CONFIG)

        # Decks and models mirror realistic structures
        self.decks: Dict[int, Dict] = {
            1: {"id": 1, "name": "Default", "card_count": 1, "is_filtered": False},
            2: {
                "id": 2,
                "name": "Languages::Spanish",
                "card_count": 2,
                "is_filtered": False,
            },
            3: {
                "id": 3,
                "name": "Languages::Japanese",
                "card_count": 1,
                "is_filtered": False,
            },
            4: {
                "id": 4,
                "name": "Languages::Core",
                "card_count": 2,
                "is_filtered": False,
            },
            5: {
                "id": 5,
                "name": "Personal::Learning",
                "card_count": 1,
                "is_filtered": True,
            },
            6: {
                "id": 6,
                "name": "Archive::Old",
                "card_count": 0,
                "is_filtered": False,
            },
        }

        self.models: Dict[str, Dict] = {
            "Basic": {
                "id": 1,
                "name": "Basic",
                "flds": [{"name": "Front"}, {"name": "Back"}],
                "tmpls": [
                    {
                        "name": "Card 1",
                        "qfmt": "{{Front}}",
                        "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
                    }
                ],
            },
            "Cloze": {
                "id": 2,
                "name": "Cloze",
                "flds": [{"name": "Text"}, {"name": "Extra"}],
                "tmpls": [
                    {"name": "Cloze 1", "qfmt": "{{cloze:Text}}", "afmt": "{{Extra}}"},
                    {"name": "Cloze 2", "qfmt": "{{cloze:Text}}", "afmt": "{{Extra}}"},
                ],
            },
            "Sentence": {
                "id": 3,
                "name": "Sentence",
                "flds": [
                    {"name": "Sentence"},
                    {"name": "Meaning"},
                    {"name": "Example"},
                ],
                "tmpls": [
                    {
                        "name": "Reading",
                        "qfmt": "{{Sentence}}",
                        "afmt": "{{FrontSide}}<hr id=answer>{{Meaning}}<br>{{Example}}",
                    }
                ],
            },
        }

        # Notes and cards include multiple decks, scheduling states, and restricted tags
        self.notes: Dict[int, Dict] = {
            1: {
                "id": 1,
                "model_name": "Basic",
                "fields": {"Front": "How are you?", "Back": "¿Cómo estás?"},
                "tags": ["spanish", "travel"],
                "card_count": 1,
            },
            2: {
                "id": 2,
                "model_name": "Basic",
                "fields": {"Front": "Good morning", "Back": "Buenos días"},
                "tags": ["spanish", "common"],
                "card_count": 1,
            },
            3: {
                "id": 3,
                "model_name": "Cloze",
                "fields": {
                    "Text": "The capital of Spain is {{c1::Madrid}}.",
                    "Extra": "Geography fact",
                },
                "tags": ["spanish", "locked"],
                "card_count": 2,
            },
            4: {
                "id": 4,
                "model_name": "Sentence",
                "fields": {
                    "Sentence": "I am learning with MCP.",
                    "Meaning": "Using a mock Anki bridge",
                    "Example": "Model Context Protocol helps testing.",
                },
                "tags": ["personal", "shared"],
                "card_count": 1,
            },
            5: {
                "id": 5,
                "model_name": "Basic",
                "fields": {"Front": "Welcome", "Back": "Bienvenido"},
                "tags": ["onboarding"],
                "card_count": 1,
            },
            6: {
                "id": 6,
                "model_name": "Basic",
                "fields": {"Front": "ありがとう", "Back": "Thank you"},
                "tags": ["japanese", "archived"],
                "card_count": 1,
            },
        }

        self.note_decks: Dict[int, str] = {
            1: "Languages::Spanish",
            2: "Languages::Spanish",
            3: "Languages::Core",
            4: "Personal::Learning",
            5: "Default",
            6: "Languages::Japanese",
        }

        self.cards_by_note: Dict[int, List[Dict]] = {
            1: [
                {
                    "id": 101,
                    "note_id": 1,
                    "deck_name": "Languages::Spanish",
                    "type": 2,
                    "queue": 2,
                    "due": 182,
                    "interval": 21,
                    "ease_factor": 2450,
                    "reviews": 14,
                    "lapses": 1,
                    "last_review": 1710000,
                }
            ],
            2: [
                {
                    "id": 102,
                    "note_id": 2,
                    "deck_name": "Languages::Spanish",
                    "type": 0,
                    "queue": 0,
                    "due": 0,
                    "interval": 0,
                    "ease_factor": 2500,
                    "reviews": 0,
                    "lapses": 0,
                    "last_review": 0,
                }
            ],
            3: [
                {
                    "id": 103,
                    "note_id": 3,
                    "deck_name": "Languages::Core",
                    "type": 0,
                    "queue": 0,
                    "due": 1,
                    "interval": 0,
                    "ease_factor": 2500,
                    "reviews": 0,
                    "lapses": 0,
                    "last_review": 0,
                },
                {
                    "id": 104,
                    "note_id": 3,
                    "deck_name": "Languages::Core",
                    "type": 2,
                    "queue": 2,
                    "due": 12,
                    "interval": 45,
                    "ease_factor": 2600,
                    "reviews": 18,
                    "lapses": 0,
                    "last_review": 1715000,
                },
            ],
            4: [
                {
                    "id": 105,
                    "note_id": 4,
                    "deck_name": "Personal::Learning",
                    "type": 1,
                    "queue": 1,
                    "due": 3,
                    "interval": 4,
                    "ease_factor": 2200,
                    "reviews": 2,
                    "lapses": 0,
                    "last_review": 1719000,
                }
            ],
            5: [
                {
                    "id": 106,
                    "note_id": 5,
                    "deck_name": "Default",
                    "type": 2,
                    "queue": 2,
                    "due": 5,
                    "interval": 30,
                    "ease_factor": 2500,
                    "reviews": 10,
                    "lapses": 1,
                    "last_review": 1718800,
                }
            ],
            6: [
                {
                    "id": 107,
                    "note_id": 6,
                    "deck_name": "Languages::Japanese",
                    "type": 1,
                    "queue": 1,
                    "due": 2,
                    "interval": 2,
                    "ease_factor": 2100,
                    "reviews": 3,
                    "lapses": 1,
                    "last_review": 1718700,
                }
            ],
        }

        self.next_deck_id = max(self.decks.keys()) + 1
        self.next_note_id = max(self.notes.keys()) + 1
        self.next_model_id = max(model["id"] for model in self.models.values()) + 1
        self.next_card_id = (
            max(card["id"] for cards in self.cards_by_note.values() for card in cards)
            + 1
        )

    async def list_decks(self) -> List[Dict]:
        """List all decks filtered by permissions."""
        decks = [deepcopy(deck) for deck in self.decks.values()]
        return self.permissions.filter_decks(decks)

    async def get_deck_info(self, deck_name: str) -> Dict:
        """Get details for a specific deck."""
        self.permissions.check_deck_permission(deck_name, PermissionAction.READ)
        deck = self._get_deck_by_name(deck_name)
        if not deck:
            raise ValueError(f"Deck not found: {deck_name}")

        cards = self._cards_for_deck(deck_name)
        new_count = len([card for card in cards if card["type"] == 0])
        learning_count = len([card for card in cards if card["type"] == 1])
        review_count = len([card for card in cards if card["type"] == 2])

        return {
            "id": deck["id"],
            "name": deck_name,
            "card_count": len(cards),
            "new_count": new_count,
            "learning_count": learning_count,
            "review_count": review_count,
            "is_filtered": deck.get("is_filtered", False),
            "config": {
                "description": f"Mock configuration for {deck_name}",
                "review_order": "new/review",
            },
        }

    async def search_notes(self, query: str, limit: int = 50) -> List[Dict]:
        """Search notes by tag, deck, model, or substring."""
        results = []
        query_lower = query.lower()

        for note_id, note in self.notes.items():
            deck_name = self.note_decks.get(note_id, "")
            if self._matches_query(note, deck_name, query_lower):
                results.append(deepcopy(note))
            if len(results) >= limit:
                break

        return results

    async def get_note(self, note_id: int) -> Dict:
        """Return a single note."""
        if note_id not in self.notes:
            raise ValueError(f"Note not found: {note_id}")
        return deepcopy(self.notes[note_id])

    async def get_cards_for_note(self, note_id: int) -> List[Dict]:
        """Return all cards for a note."""
        if note_id not in self.notes:
            raise ValueError(f"Note not found: {note_id}")
        return deepcopy(self.cards_by_note.get(note_id, []))

    async def get_review_stats(self, deck_name: Optional[str] = None) -> Dict:
        """Aggregate review stats for a deck or globally."""
        if deck_name:
            self.permissions.check_deck_permission(deck_name, PermissionAction.READ)
            cards = self._cards_for_deck(deck_name)
        else:
            allowed_decks = [deck["name"] for deck in await self.list_decks()]
            cards = [
                card
                for note_id, deck in self.note_decks.items()
                for card in self.cards_by_note.get(note_id, [])
                if deck in allowed_decks
            ]

        total_cards = len(cards)
        new_cards = len([card for card in cards if card["type"] == 0])
        learning_cards = len([card for card in cards if card["type"] == 1])
        review_cards = len([card for card in cards if card["type"] == 2])
        mature_cards = len([card for card in cards if card["interval"] >= 21])

        return {
            "deck_name": deck_name or "All Decks",
            "total_cards": total_cards,
            "new_cards": new_cards,
            "learning_cards": learning_cards,
            "review_cards": review_cards,
            "mature_cards": mature_cards,
        }

    async def create_deck(self, deck_name: str) -> Dict:
        """Create a new deck if permitted."""
        self.permissions.check_deck_permission(deck_name, PermissionAction.CREATE)

        existing = self._get_deck_by_name(deck_name)
        if existing:
            return {
                "id": existing["id"],
                "name": deck_name,
                "created": False,
                "config": {},
            }

        deck_id = self.next_deck_id
        self.next_deck_id += 1
        deck = {"id": deck_id, "name": deck_name, "card_count": 0, "is_filtered": False}
        self.decks[deck_id] = deck
        return {
            "id": deck_id,
            "name": deck_name,
            "created": True,
            "config": {},
        }

    async def create_note_type(
        self, name: str, fields: List[str], templates: List[Dict]
    ):
        """Create a new note type with provided fields/templates."""
        self.permissions.check_note_type_permission(name, PermissionAction.CREATE)
        if name in self.models:
            raise ValueError(f"Model already exists: {name}")

        if not fields:
            raise ValueError("At least one field is required")
        if not templates:
            raise ValueError("At least one template is required")

        model_id = self.next_model_id
        self.next_model_id += 1

        model_fields = [{"name": field} for field in fields]
        self.models[name] = {
            "id": model_id,
            "name": name,
            "flds": model_fields,
            "tmpls": templates,
        }

        return {
            "id": model_id,
            "name": name,
            "field_count": len(fields),
            "template_count": len(templates),
            "created": True,
        }

    async def create_note(
        self,
        model_name: str,
        fields: Dict,
        deck_name: str,
        tags: Optional[List[str]] = None,
    ):
        """Create a new note and associated cards."""
        self.permissions.check_deck_permission(deck_name, PermissionAction.WRITE)
        if tags:
            self.permissions.check_tag_permission(tags, PermissionAction.WRITE)
        self.permissions.check_note_type_permission(model_name, PermissionAction.WRITE)

        model = self.models.get(model_name)
        if not model:
            raise ValueError(f"Model not found: {model_name}")

        deck = self._get_deck_by_name(deck_name)
        if not deck:
            raise ValueError(f"Deck not found: {deck_name}")

        note_id = self.next_note_id
        self.next_note_id += 1

        card_count = max(1, len(model.get("tmpls", [])))
        note = {
            "id": note_id,
            "model_name": model_name,
            "fields": fields.copy(),
            "tags": tags or [],
            "card_count": card_count,
        }
        self.notes[note_id] = note
        self.note_decks[note_id] = deck_name

        self.cards_by_note[note_id] = self._generate_cards(
            note_id, deck_name, card_count
        )
        deck["card_count"] += card_count

        return deepcopy(note)

    async def update_note(
        self,
        note_id: int,
        fields: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        """Update fields/tags on an existing note."""
        if note_id not in self.notes:
            raise ValueError(f"Note not found: {note_id}")

        note = self.notes[note_id]
        deck_name = self.note_decks.get(note_id, "")

        self.permissions.check_deck_permission(deck_name, PermissionAction.WRITE)
        self.permissions.check_tag_permission(
            note.get("tags", []), PermissionAction.WRITE
        )
        if tags is not None:
            self.permissions.check_tag_permission(tags, PermissionAction.WRITE)

        if fields:
            note["fields"].update(fields)
        if tags is not None:
            note["tags"] = tags

        return deepcopy(note)

    async def delete_note(self, note_id: int) -> Dict:
        """Delete a note and its cards."""
        if note_id not in self.notes:
            raise ValueError(f"Note not found: {note_id}")

        note = self.notes[note_id]
        deck_name = self.note_decks.get(note_id, "")

        self.permissions.check_tag_permission(
            note.get("tags", []), PermissionAction.DELETE
        )
        self.permissions.check_deck_permission(deck_name, PermissionAction.DELETE)

        removed_cards = self.cards_by_note.pop(note_id, [])
        deck = self._get_deck_by_name(deck_name)
        if deck:
            deck["card_count"] = max(0, deck["card_count"] - len(removed_cards))

        del self.notes[note_id]
        self.note_decks.pop(note_id, None)

        return {
            "note_id": note_id,
            "deleted": True,
            "cards_deleted": len(removed_cards),
        }

    def _get_deck_by_name(self, deck_name: str) -> Optional[Dict]:
        """Find a deck by name."""
        for deck in self.decks.values():
            if deck["name"] == deck_name:
                return deck
        return None

    def _cards_for_deck(self, deck_name: str) -> List[Dict]:
        """Return all cards for a given deck name."""
        cards = []
        for note_id, mapped_deck in self.note_decks.items():
            if mapped_deck == deck_name:
                cards.extend(deepcopy(self.cards_by_note.get(note_id, [])))
        return cards

    def _matches_query(self, note: Dict, deck_name: str, query_lower: str) -> bool:
        """Simplified query matching for tags, deck, model, or text."""
        if query_lower.startswith("tag:"):
            tag_query = query_lower.split("tag:", 1)[1].strip()
            return any(tag_query == tag.lower() for tag in note.get("tags", []))
        if query_lower.startswith("deck:"):
            deck_query = query_lower.split("deck:", 1)[1].strip()
            return deck_query in deck_name.lower()
        if query_lower.startswith("model:"):
            model_query = query_lower.split("model:", 1)[1].strip()
            return model_query == note.get("model_name", "").lower()

        # Fallback: match text in fields or tags
        in_tags = any(query_lower in tag.lower() for tag in note.get("tags", []))
        in_fields = any(
            query_lower in str(value).lower()
            for value in note.get("fields", {}).values()
        )
        in_deck = query_lower in deck_name.lower()
        return in_tags or in_fields or in_deck

    def _generate_cards(self, note_id: int, deck_name: str, count: int) -> List[Dict]:
        """Generate card stubs for a new note."""
        cards: List[Dict] = []
        for i in range(count):
            cards.append(
                {
                    "id": self.next_card_id + i,
                    "note_id": note_id,
                    "deck_name": deck_name,
                    "type": 0,
                    "queue": 0,
                    "due": 0,
                    "interval": 0,
                    "ease_factor": 2500,
                    "reviews": 0,
                    "lapses": 0,
                    "last_review": 0,
                }
            )
        self.next_card_id += count
        return cards


async def main():
    """Entrypoint used by `python -m ankimcp.bridge`."""
    logger.info("Starting AnkiMCP bridge with %d tools", len(AVAILABLE_TOOLS))
    bridge_anki = BridgeAnkiInterface()
    try:
        await server_main(bridge_anki)
    except PermissionError as exc:
        logger.error("Permission error starting server: %s", exc)
        raise


def configure_logging():
    """Initialize logging for the standalone server."""
    log_level = os.getenv("ANKIMCP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


if __name__ == "__main__":
    configure_logging()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bridge server stopped by user")
