"""Tests for permission enforcement in AnkiInterface."""

import pytest

from ankimcp.permissions import PermissionError, PermissionManager
from tests.test_utils import MockAnkiInterface


class TestAnkiInterfacePermissions:
    """Test permission enforcement in AnkiInterface."""

    @pytest.fixture
    def restrictive_anki(self):
        """Create AnkiInterface with restrictive permissions."""
        anki = MockAnkiInterface()
        # Override with restrictive permissions
        anki.permissions = PermissionManager(
            {
                "permissions": {
                    "global": {"read": True, "write": False, "delete": False},
                    "mode": "denylist",
                    "deck_permissions": {"denylist": []},
                    "protected_decks": ["Default"],
                }
            }
        )
        return anki

    @pytest.fixture
    def allowlist_anki(self):
        """Create AnkiInterface with allowlist permissions."""
        anki = MockAnkiInterface()
        anki.permissions = PermissionManager(
            {
                "permissions": {
                    "global": {"read": True, "write": True, "delete": True},
                    "mode": "allowlist",
                    "deck_permissions": {
                        "allowlist": ["Spanish"],
                        "denylist": [],
                    },
                    "protected_decks": [],
                }
            }
        )
        return anki

    @pytest.fixture
    def tag_restricted_anki(self):
        """Create AnkiInterface with tag restrictions."""
        anki = MockAnkiInterface()
        anki.permissions = PermissionManager(
            {
                "permissions": {
                    "global": {"read": True, "write": True, "delete": True},
                    "mode": "denylist",
                    "deck_permissions": {"allowlist": [], "denylist": []},
                    "protected_decks": [],  # No protected decks for this test
                    "tag_restrictions": {
                        "protected_tags": ["important"],
                        "readonly_tags": ["archive"],
                    },
                }
            }
        )
        # Add notes with restricted tags
        anki.notes[2] = {
            "id": 2,
            "model_name": "Basic",
            "fields": {"Front": "Important", "Back": "Importante"},
            "tags": ["spanish", "important"],
            "card_count": 1,
        }
        anki.notes[3] = {
            "id": 3,
            "model_name": "Basic",
            "fields": {"Front": "Archived", "Back": "Archivado"},
            "tags": ["spanish", "archive"],
            "card_count": 1,
        }
        return anki

    @pytest.mark.asyncio
    async def test_list_decks_with_permissions(self, allowlist_anki):
        """Test list_decks filters based on permissions."""
        decks = await allowlist_anki.list_decks()
        # Should only see Spanish deck in allowlist mode
        assert len(decks) == 1
        assert decks[0]["name"] == "Spanish"

    @pytest.mark.asyncio
    async def test_get_deck_info_denied(self, allowlist_anki):
        """Test get_deck_info with denied access."""
        # Spanish should work (in allowlist)
        info = await allowlist_anki.get_deck_info("Spanish")
        assert info["name"] == "Spanish"

        # Default should fail (not in allowlist)
        with pytest.raises(PermissionError, match="not in the allowlist"):
            await allowlist_anki.get_deck_info("Default")

    @pytest.mark.asyncio
    async def test_create_deck_denied(self, restrictive_anki):
        """Test create_deck with write disabled."""
        with pytest.raises(PermissionError, match="Global write permission denied"):
            await restrictive_anki.create_deck("New Deck")

    @pytest.mark.asyncio
    async def test_create_deck_protected(self, allowlist_anki):
        """Test creating deck not in allowlist."""
        # Can't create decks not in allowlist
        with pytest.raises(PermissionError, match="not in the allowlist"):
            await allowlist_anki.create_deck("German")

    @pytest.mark.asyncio
    async def test_create_note_denied(self, restrictive_anki):
        """Test create_note with write disabled."""
        with pytest.raises(PermissionError, match="Global write permission denied"):
            await restrictive_anki.create_note(
                model_name="Basic",
                fields={"Front": "Test", "Back": "Prueba"},
                deck_name="Spanish",
            )

    @pytest.mark.asyncio
    async def test_create_note_wrong_deck(self, allowlist_anki):
        """Test creating note in non-allowed deck."""
        with pytest.raises(PermissionError, match="not in the allowlist"):
            await allowlist_anki.create_note(
                model_name="Basic",
                fields={"Front": "Test", "Back": "Test"},
                deck_name="Default",  # Not in allowlist
            )

    @pytest.mark.asyncio
    async def test_create_note_protected_tags(self, tag_restricted_anki):
        """Test creating note with protected tags."""
        # Should fail with protected tag
        with pytest.raises(PermissionError, match="protected tags"):
            await tag_restricted_anki.create_note(
                model_name="Basic",
                fields={"Front": "Test", "Back": "Prueba"},
                deck_name="Spanish",
                tags=["important"],  # Protected tag
            )

    @pytest.mark.asyncio
    async def test_update_note_denied(self, restrictive_anki):
        """Test update_note with write disabled."""
        with pytest.raises(PermissionError, match="Global write permission denied"):
            await restrictive_anki.update_note(1, fields={"Front": "Updated"})

    @pytest.mark.asyncio
    async def test_update_note_protected_tags(self, tag_restricted_anki):
        """Test updating note with protected tags."""
        # Can't update note with protected tag
        with pytest.raises(PermissionError, match="protected tags"):
            await tag_restricted_anki.update_note(
                2,  # Has "important" tag
                fields={"Front": "Updated"},
            )

        # Can't add protected tag to existing note
        with pytest.raises(PermissionError, match="protected tags"):
            await tag_restricted_anki.update_note(
                1,
                tags=["spanish", "important"],
            )

    @pytest.mark.asyncio
    async def test_update_note_readonly_tags(self, tag_restricted_anki):
        """Test updating note with readonly tags."""
        # Can't update note with readonly tag
        with pytest.raises(PermissionError, match="readonly tags"):
            await tag_restricted_anki.update_note(
                3,  # Has "archive" tag
                fields={"Front": "Updated"},
            )

    @pytest.mark.asyncio
    async def test_delete_note_denied(self, restrictive_anki):
        """Test delete_note with delete disabled."""
        with pytest.raises(PermissionError, match="Global delete permission denied"):
            await restrictive_anki.delete_note(1)

    @pytest.mark.asyncio
    async def test_delete_note_protected_tags(self, tag_restricted_anki):
        """Test deleting note with protected tags."""
        # Can't delete note with protected tag
        with pytest.raises(PermissionError, match="protected tags"):
            await tag_restricted_anki.delete_note(2)  # Has "important" tag

        # Can't delete note with readonly tag either
        with pytest.raises(PermissionError, match="readonly tags"):
            await tag_restricted_anki.delete_note(3)  # Has "archive" tag

    @pytest.mark.asyncio
    async def test_protected_deck(self):
        """Test protected deck functionality."""
        anki = MockAnkiInterface()
        anki.permissions = PermissionManager(
            {
                "permissions": {
                    "global": {"read": True, "write": True, "delete": True},
                    "mode": "denylist",
                    "protected_decks": ["Default"],
                }
            }
        )

        # Can read protected deck
        info = await anki.get_deck_info("Default")
        assert info["name"] == "Default"

        # Can't create in protected deck (treated as modification)
        with pytest.raises(PermissionError, match="protected"):
            await anki.create_deck("Default")

    @pytest.mark.asyncio
    async def test_note_type_permissions(self):
        """Test note type permission enforcement."""
        anki = MockAnkiInterface()
        anki.permissions = PermissionManager(
            {
                "permissions": {
                    "global": {"read": True, "write": True, "delete": True},
                    "mode": "denylist",
                    "note_type_permissions": {
                        "allow_create": False,
                        "allowed_types": ["Basic"],
                    },
                }
            }
        )

        # Can use allowed type
        note = await anki.create_note(
            model_name="Basic",
            fields={"Front": "Test", "Back": "Prueba"},
            deck_name="Spanish",
        )
        assert note["model_name"] == "Basic"

        # Can't create new note types
        with pytest.raises(PermissionError, match="Creating new note types"):
            await anki.create_note_type(
                "Custom",
                ["Front", "Back"],
                [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{Back}}"}],
            )

    @pytest.mark.asyncio
    async def test_complex_permission_scenario(self):
        """Test complex real-world permission scenario."""
        anki = MockAnkiInterface()
        anki.permissions = PermissionManager(
            {
                "permissions": {
                    "global": {"read": True, "write": True, "delete": False},
                    "mode": "allowlist",
                    "deck_permissions": {
                        "allowlist": ["Languages::*", "Study::*"],
                    },
                    "protected_decks": ["Languages::Core"],
                    "tag_restrictions": {
                        "protected_tags": ["verified", "teacher"],
                        "readonly_tags": ["2023", "old"],
                    },
                    "note_type_permissions": {
                        "allow_create": True,
                        "allowed_types": ["Basic", "Cloze"],
                    },
                }
            }
        )

        # Add test decks (add Spanish deck after asserting French can be created)
        anki.decks[4] = {
            "id": 4,
            "name": "Languages::Core",
            "card_count": 100,
            "is_filtered": False,
        }
        anki.decks[5] = {
            "id": 5,
            "name": "Personal",
            "card_count": 50,
            "is_filtered": False,
        }

        # List decks should only show allowed patterns
        decks = await anki.list_decks()
        deck_names = [d["name"] for d in decks]
        assert "Languages::Core" in deck_names
        assert "Personal" not in deck_names  # Not in allowlist
        assert "Default" not in deck_names  # Not in allowlist

        # Can create deck matching pattern
        result = await anki.create_deck("Languages::French")
        assert result["created"] is True

        # Create Spanish deck for note creation test
        spanish_result = await anki.create_deck("Languages::Spanish")
        assert spanish_result["created"] is True

        # Can't create deck not matching pattern
        with pytest.raises(PermissionError, match="not in the allowlist"):
            await anki.create_deck("Personal::New")

        # Can't modify protected deck
        with pytest.raises(PermissionError, match="protected"):
            await anki.create_deck("Languages::Core")

        # Can create note with allowed type in allowed deck
        note = await anki.create_note(
            model_name="Basic",
            fields={"Front": "Hello", "Back": "Hola"},
            deck_name="Languages::Spanish",
            tags=["greeting", "common"],
        )
        assert note["id"] > 1

        # Can't delete anything (globally disabled)
        with pytest.raises(PermissionError, match="Global delete permission denied"):
            await anki.delete_note(note["id"])
