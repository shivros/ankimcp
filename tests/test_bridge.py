"""Tests for the standalone bridge mock interface."""

import pytest

from ankimcp.bridge import BridgeAnkiInterface
from ankimcp.permissions import PermissionError


@pytest.mark.asyncio
async def test_bridge_filters_decks():
    """Archive deck should be hidden by allowlist rules."""
    bridge = BridgeAnkiInterface()
    decks = await bridge.list_decks()
    deck_names = {deck["name"] for deck in decks}

    assert "Archive::Old" not in deck_names
    assert "Languages::Spanish" in deck_names


@pytest.mark.asyncio
async def test_bridge_creates_note_in_allowed_deck():
    """Creating a note in an allowed deck should succeed and increment counts."""
    bridge = BridgeAnkiInterface()
    created = await bridge.create_note(
        "Basic",
        {"Front": "Test", "Back": "Prueba"},
        "Languages::Spanish",
        tags=["spanish"],
    )

    assert created["model_name"] == "Basic"
    assert created["fields"]["Front"] == "Test"

    deck_info = await bridge.get_deck_info("Languages::Spanish")
    assert deck_info["card_count"] == 3  # initial 2 + 1 new card


@pytest.mark.asyncio
async def test_bridge_denies_disallowed_deck():
    """Creating a note in a disallowed deck should raise a permission error."""
    bridge = BridgeAnkiInterface()

    with pytest.raises(PermissionError):
        await bridge.create_note(
            "Basic",
            {"Front": "Blocked", "Back": "Denied"},
            "Archive::Old",
        )


@pytest.mark.asyncio
async def test_bridge_denies_protected_tags_on_update():
    """Protected tags should block updates."""
    bridge = BridgeAnkiInterface()

    with pytest.raises(PermissionError):
        await bridge.update_note(3, fields={"Text": "Changed"})


@pytest.mark.asyncio
async def test_bridge_denies_delete_with_readonly_tags():
    """Readonly tags should block deletion."""
    bridge = BridgeAnkiInterface()

    with pytest.raises(PermissionError):
        await bridge.delete_note(6)
