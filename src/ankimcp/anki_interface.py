"""Interface for accessing Anki data."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

try:
    # When running as an Anki addon
    from anki.cards import Card
    from anki.collection import Collection
    from anki.notes import Note
    from aqt import mw

    ANKI_AVAILABLE = True
except ImportError:
    # When running standalone or testing
    ANKI_AVAILABLE = False
    mw = None
    if not TYPE_CHECKING:
        Collection = Any
        Note = Any
        Card = Any


class AnkiInterface:
    """Interface for accessing Anki collection data."""

    def __init__(self, collection: Optional["Collection"] = None):
        """Initialize with a collection (uses mw.col if not provided)."""
        if collection:
            self.col = collection
        elif ANKI_AVAILABLE and mw and mw.col:
            self.col = mw.col
        else:
            raise RuntimeError("No Anki collection available")

    async def list_decks(self) -> List[Dict[str, Any]]:
        """List all available decks."""
        decks = []
        for deck_id in self.col.decks.all_names_and_ids():
            deck = self.col.decks.get(deck_id.id)  # type: ignore
            if deck:
                decks.append(
                    {
                        "id": deck_id.id,
                        "name": deck_id.name,
                        "card_count": len(self.col.decks.cids(deck_id.id)),  # type: ignore
                        "is_filtered": deck.get("dyn", 0) != 0,
                    }
                )
        return decks

    async def get_deck_info(self, deck_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific deck."""
        deck_id = self.col.decks.id_for_name(deck_name)
        if not deck_id:
            raise ValueError(f"Deck not found: {deck_name}")

        deck = self.col.decks.get(deck_id)
        if not deck:
            raise ValueError(f"Deck not found: {deck_name}")

        card_ids = self.col.decks.cids(deck_id)  # type: ignore

        # Get review statistics
        new_count = len([cid for cid in card_ids if self.col.get_card(cid).type == 0])
        learning_count = len(
            [cid for cid in card_ids if self.col.get_card(cid).type == 1]
        )
        review_count = len(
            [cid for cid in card_ids if self.col.get_card(cid).type == 2]
        )

        return {
            "id": deck_id,
            "name": deck_name,
            "card_count": len(card_ids),
            "new_count": new_count,
            "learning_count": learning_count,
            "review_count": review_count,
            "is_filtered": deck.get("dyn", 0) != 0,
            "config": deck,
        }

    async def search_notes(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for notes using Anki's search syntax."""
        note_ids = self.col.find_notes(query)[:limit]
        notes = []

        for nid in note_ids:
            note = self.col.get_note(nid)  # type: ignore
            notes.append(await self._note_to_dict(note))

        return notes

    async def get_note(self, note_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific note."""
        note = self.col.get_note(note_id)  # type: ignore
        return await self._note_to_dict(note)

    async def get_cards_for_note(self, note_id: int) -> List[Dict[str, Any]]:
        """Get all cards associated with a note."""
        note = self.col.get_note(note_id)  # type: ignore
        cards = []

        for card_id in note.card_ids():
            card = self.col.get_card(card_id)
            cards.append(await self._card_to_dict(card))

        return cards

    async def get_review_stats(self, deck_name: Optional[str] = None) -> Dict[str, Any]:
        """Get review statistics for a deck or overall."""
        if deck_name:
            deck_id = self.col.decks.id_for_name(deck_name)
            if not deck_id:
                raise ValueError(f"Deck not found: {deck_name}")
            card_ids = self.col.decks.cids(deck_id)  # type: ignore
        else:
            card_ids = self.col.find_cards("")

        total_cards = len(card_ids)
        new_cards = 0
        learning_cards = 0
        review_cards = 0

        for cid in card_ids:
            card = self.col.get_card(cid)
            if card.type == 0:
                new_cards += 1
            elif card.type == 1:
                learning_cards += 1
            elif card.type == 2:
                review_cards += 1

        return {
            "deck_name": deck_name or "All Decks",
            "total_cards": total_cards,
            "new_cards": new_cards,
            "learning_cards": learning_cards,
            "review_cards": review_cards,
            "mature_cards": len(
                [cid for cid in card_ids if self.col.get_card(cid).ivl >= 21]
            ),
        }

    async def _note_to_dict(self, note: "Note") -> Dict[str, Any]:
        """Convert a note to a dictionary."""
        model = note.note_type()
        fields = {}

        if model:
            for i, field in enumerate(model["flds"]):
                fields[field["name"]] = note.fields[i]

        return {
            "id": note.id,
            "model_name": model["name"] if model else "Unknown",
            "fields": fields,
            "tags": note.tags,
            "card_count": len(note.card_ids()),
        }

    async def _card_to_dict(self, card: "Card") -> Dict[str, Any]:
        """Convert a card to a dictionary."""
        card.note()  # Ensure note is loaded
        deck_name = self.col.decks.name(card.did)

        return {
            "id": card.id,
            "note_id": card.nid,
            "deck_name": deck_name,
            "type": card.type,  # 0=new, 1=learning, 2=review
            "queue": card.queue,
            "due": card.due,
            "interval": card.ivl,
            "ease_factor": card.factor,
            "reviews": card.reps,
            "lapses": card.lapses,
            "last_review": getattr(card, "last_review", 0),
        }

    async def create_deck(self, deck_name: str) -> Dict[str, Any]:
        """Create a new deck."""
        deck_id = self.col.decks.id(deck_name)  # This creates if doesn't exist
        deck = self.col.decks.get(deck_id)
        
        return {
            "id": deck_id,
            "name": deck_name,
            "created": True,
            "config": deck,
        }

    async def create_note_type(
        self, 
        name: str, 
        fields: List[str], 
        templates: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Create a new note type (model)."""
        models = self.col.models
        
        # Create a new model
        model = models.new(name)
        
        # Add fields
        for field_name in fields:
            field = models.new_field(field_name)
            models.add_field(model, field)
        
        # Add templates (card types)
        for template in templates:
            t = models.new_template(template.get("name", "Card 1"))
            t["qfmt"] = template.get("qfmt", "{{" + fields[0] + "}}")
            t["afmt"] = template.get("afmt", "{{FrontSide}}\n\n<hr id=answer>\n\n{{" + fields[-1] + "}}")
            models.add_template(model, t)
        
        # Save the model
        models.save(model)
        
        return {
            "id": model["id"],
            "name": model["name"],
            "field_count": len(model["flds"]),
            "template_count": len(model["tmpls"]),
            "created": True,
        }

    async def create_note(
        self, 
        model_name: str, 
        fields: Dict[str, str], 
        deck_name: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new note."""
        # Get model
        model_id = self.col.models.id_for_name(model_name)
        if not model_id:
            raise ValueError(f"Model not found: {model_name}")
        
        model = self.col.models.get(model_id)
        
        # Get deck
        deck_id = self.col.decks.id_for_name(deck_name)
        if not deck_id:
            raise ValueError(f"Deck not found: {deck_name}")
        
        # Create note
        note = self.col.new_note(model)
        
        # Set fields
        for field in model["flds"]:
            field_name = field["name"]
            if field_name in fields:
                note[field_name] = fields[field_name]
        
        # Set tags
        if tags:
            note.tags = tags
        
        # Add to collection
        self.col.add_note(note, deck_id)
        
        return await self._note_to_dict(note)

    async def update_note(
        self, 
        note_id: int, 
        fields: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update an existing note."""
        note = self.col.get_note(note_id)
        
        # Update fields
        if fields:
            model = note.note_type()
            for field in model["flds"]:
                field_name = field["name"]
                if field_name in fields:
                    note[field_name] = fields[field_name]
        
        # Update tags
        if tags is not None:
            note.tags = tags
        
        # Save changes
        self.col.update_note(note)
        
        return await self._note_to_dict(note)

    async def delete_note(self, note_id: int) -> Dict[str, Any]:
        """Delete a note and all its cards."""
        note = self.col.get_note(note_id)
        card_count = len(note.card_ids())
        
        # Remove the note (this also removes all associated cards)
        self.col.remove_notes([note_id])
        
        return {
            "note_id": note_id,
            "deleted": True,
            "cards_deleted": card_count,
        }
