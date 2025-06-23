"""Tests for the Anki interface."""

import pytest

from ankimcp.__main__ import MockAnkiInterface


@pytest.fixture
def mock_anki():
    """Provide a mock Anki interface."""
    return MockAnkiInterface()


@pytest.mark.asyncio
async def test_list_decks(mock_anki):
    """Test listing decks."""
    decks = await mock_anki.list_decks()
    assert len(decks) == 2
    assert decks[0]["name"] == "Default"
    assert decks[1]["name"] == "Spanish"


@pytest.mark.asyncio
async def test_get_deck_info(mock_anki):
    """Test getting deck info."""
    info = await mock_anki.get_deck_info("Default")
    assert info["name"] == "Default"
    assert info["card_count"] == 10
    assert info["new_count"] == 3

    # Test non-existent deck
    with pytest.raises(ValueError):
        await mock_anki.get_deck_info("NonExistent")


@pytest.mark.asyncio
async def test_search_notes(mock_anki):
    """Test searching notes."""
    notes = await mock_anki.search_notes("tag:spanish")
    assert len(notes) == 1
    assert notes[0]["fields"]["Front"] == "Hello"


@pytest.mark.asyncio
async def test_get_note(mock_anki):
    """Test getting a specific note."""
    note = await mock_anki.get_note(1)
    assert note["id"] == 1
    assert note["model_name"] == "Basic"

    # Test non-existent note
    with pytest.raises(ValueError):
        await mock_anki.get_note(999)


@pytest.mark.asyncio
async def test_get_cards_for_note(mock_anki):
    """Test getting cards for a note."""
    cards = await mock_anki.get_cards_for_note(1)
    assert len(cards) == 1
    assert cards[0]["note_id"] == 1
    assert cards[0]["deck_name"] == "Spanish"


@pytest.mark.asyncio
async def test_get_review_stats(mock_anki):
    """Test getting review statistics."""
    stats = await mock_anki.get_review_stats()
    assert stats["deck_name"] == "All Decks"
    assert stats["total_cards"] == 60

    stats = await mock_anki.get_review_stats("Default")
    assert stats["deck_name"] == "Default"


@pytest.mark.asyncio
async def test_create_deck(mock_anki):
    """Test creating a new deck."""
    # Create a new deck
    result = await mock_anki.create_deck("Japanese")
    assert result["name"] == "Japanese"
    assert result["created"] is True
    assert "id" in result

    # Verify deck was created
    decks = await mock_anki.list_decks()
    deck_names = [d["name"] for d in decks]
    assert "Japanese" in deck_names

    # Try to create the same deck again
    result = await mock_anki.create_deck("Japanese")
    assert result["created"] is False
    assert result["name"] == "Japanese"


@pytest.mark.asyncio
async def test_create_note_type(mock_anki):
    """Test creating a new note type."""
    # Create a new note type
    fields = ["Question", "Answer", "Extra"]
    templates = [
        {
            "name": "Forward",
            "qfmt": "{{Question}}",
            "afmt": "{{FrontSide}}<hr id=answer>{{Answer}}<br>{{Extra}}",
        },
        {
            "name": "Reverse",
            "qfmt": "{{Answer}}",
            "afmt": "{{FrontSide}}<hr id=answer>{{Question}}<br>{{Extra}}",
        },
    ]

    result = await mock_anki.create_note_type("Custom", fields, templates)
    assert result["name"] == "Custom"
    assert result["field_count"] == 3
    assert result["template_count"] == 2
    assert result["created"] is True
    assert "id" in result

    # Try to create the same note type again
    with pytest.raises(ValueError, match="Model already exists"):
        await mock_anki.create_note_type("Custom", fields, templates)


@pytest.mark.asyncio
async def test_create_note(mock_anki):
    """Test creating a new note."""
    # Create a note with Basic model in Spanish deck
    fields = {"Front": "Goodbye", "Back": "Adiós"}
    tags = ["spanish", "common"]

    result = await mock_anki.create_note(
        model_name="Basic", fields=fields, deck_name="Spanish", tags=tags
    )

    assert result["model_name"] == "Basic"
    assert result["fields"] == fields
    assert result["tags"] == tags
    assert "id" in result
    assert result["card_count"] == 1

    # Verify note was created
    note = await mock_anki.get_note(result["id"])
    assert note["fields"]["Front"] == "Goodbye"
    assert note["fields"]["Back"] == "Adiós"
    assert "spanish" in note["tags"]

    # Test with non-existent model
    with pytest.raises(ValueError, match="Model not found"):
        await mock_anki.create_note(
            model_name="NonExistent", fields=fields, deck_name="Spanish"
        )

    # Test with non-existent deck
    with pytest.raises(ValueError, match="Deck not found"):
        await mock_anki.create_note(
            model_name="Basic", fields=fields, deck_name="NonExistent"
        )


@pytest.mark.asyncio
async def test_update_note(mock_anki):
    """Test updating an existing note."""
    # Get an existing note
    note = await mock_anki.get_note(1)
    original_tags = note["tags"]

    # Update fields only
    updated_fields = {"Front": "Hi", "Back": "Hola (updated)"}
    result = await mock_anki.update_note(1, fields=updated_fields)

    assert result["id"] == 1
    assert result["fields"]["Front"] == "Hi"
    assert result["fields"]["Back"] == "Hola (updated)"
    assert result["tags"] == original_tags  # Tags should remain unchanged

    # Update tags only
    new_tags = ["spanish", "greetings", "updated"]
    result = await mock_anki.update_note(1, tags=new_tags)

    assert result["tags"] == new_tags
    assert result["fields"]["Front"] == "Hi"  # Previous field update should persist

    # Update both fields and tags
    result = await mock_anki.update_note(
        1, fields={"Front": "Hello again"}, tags=["spanish", "basic"]
    )

    assert result["fields"]["Front"] == "Hello again"
    assert result["tags"] == ["spanish", "basic"]

    # Test updating non-existent note
    with pytest.raises(ValueError, match="Note not found"):
        await mock_anki.update_note(999, fields={"Front": "Test"})


@pytest.mark.asyncio
async def test_delete_note(mock_anki):
    """Test deleting a note."""
    # First create a new note to delete
    fields = {"Front": "Test", "Back": "Prueba"}
    created_note = await mock_anki.create_note(
        model_name="Basic", fields=fields, deck_name="Spanish", tags=["test"]
    )
    note_id = created_note["id"]

    # Verify the note exists
    note = await mock_anki.get_note(note_id)
    assert note["fields"]["Front"] == "Test"

    # Delete the note
    result = await mock_anki.delete_note(note_id)
    assert result["note_id"] == note_id
    assert result["deleted"] is True
    assert result["cards_deleted"] == 1

    # Verify the note no longer exists
    with pytest.raises(ValueError, match="Note not found"):
        await mock_anki.get_note(note_id)

    # Test deleting non-existent note
    with pytest.raises(ValueError, match="Note not found"):
        await mock_anki.delete_note(999)


@pytest.mark.asyncio
async def test_mutation_integration(mock_anki):
    """Test a complete workflow with multiple mutations."""
    # Create a new deck
    deck_result = await mock_anki.create_deck("Integration Test")
    assert deck_result["created"] is True

    # Create a new note type
    model_result = await mock_anki.create_note_type(
        "Integration Model",
        ["Term", "Definition", "Example"],
        [
            {
                "name": "Card 1",
                "qfmt": "{{Term}}",
                "afmt": "{{FrontSide}}<hr>{{Definition}}<br>{{Example}}",
            }
        ],
    )
    assert model_result["created"] is True

    # Create a note
    note_result = await mock_anki.create_note(
        model_name="Integration Model",
        fields={
            "Term": "Mutation",
            "Definition": "A change in data",
            "Example": "Creating, updating, or deleting records",
        },
        deck_name="Integration Test",
        tags=["programming", "database"],
    )
    note_id = note_result["id"]

    # Update the note
    update_result = await mock_anki.update_note(
        note_id,
        fields={"Example": "CRUD operations: Create, Read, Update, Delete"},
        tags=["programming", "database", "crud"],
    )
    assert "crud" in update_result["tags"]

    # Verify the updated note
    updated_note = await mock_anki.get_note(note_id)
    assert (
        updated_note["fields"]["Example"]
        == "CRUD operations: Create, Read, Update, Delete"
    )

    # Delete the note
    delete_result = await mock_anki.delete_note(note_id)
    assert delete_result["deleted"] is True
