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
