"""Tests for the permission system."""

import pytest

from ankimcp.permissions import (
    PermissionAction,
    PermissionError,
    PermissionManager,
)


class TestPermissionManager:
    """Test the PermissionManager class."""

    def test_default_config(self):
        """Test permission manager with default config."""
        config = {
            "permissions": {
                "global": {"read": True, "write": True, "delete": True},
                "mode": "denylist",
                "deck_permissions": {"allowlist": [], "denylist": []},
                "protected_decks": [],
            }
        }
        pm = PermissionManager(config)

        # Should allow all operations by default
        pm.check_deck_permission("Test Deck", PermissionAction.READ)
        pm.check_deck_permission("Test Deck", PermissionAction.WRITE)
        pm.check_deck_permission("Test Deck", PermissionAction.DELETE)

    def test_global_permissions(self):
        """Test global permission settings."""
        config = {
            "permissions": {
                "global": {"read": True, "write": False, "delete": False},
                "mode": "denylist",
                "deck_permissions": {"allowlist": [], "denylist": []},
            }
        }
        pm = PermissionManager(config)

        # Read should be allowed
        pm.check_deck_permission("Test Deck", PermissionAction.READ)

        # Write should be denied
        with pytest.raises(PermissionError, match="Global write permission denied"):
            pm.check_deck_permission("Test Deck", PermissionAction.WRITE)

        # Delete should be denied
        with pytest.raises(PermissionError, match="Global delete permission denied"):
            pm.check_deck_permission("Test Deck", PermissionAction.DELETE)

    def test_protected_decks(self):
        """Test protected deck functionality."""
        config = {
            "permissions": {
                "global": {"read": True, "write": True, "delete": True},
                "mode": "denylist",
                "protected_decks": ["Default", "Core 2000"],
            }
        }
        pm = PermissionManager(config)

        # Read should be allowed for protected decks
        pm.check_deck_permission("Default", PermissionAction.READ)

        # Write should be denied for protected decks
        with pytest.raises(PermissionError, match="Deck 'Default' is protected"):
            pm.check_deck_permission("Default", PermissionAction.WRITE)

        # Delete should be denied for protected decks
        with pytest.raises(PermissionError, match="Deck 'Core 2000' is protected"):
            pm.check_deck_permission("Core 2000", PermissionAction.DELETE)

        # Non-protected decks should allow all operations
        pm.check_deck_permission("Spanish", PermissionAction.WRITE)
        pm.check_deck_permission("Spanish", PermissionAction.DELETE)

    def test_allowlist_mode(self):
        """Test allowlist mode."""
        config = {
            "permissions": {
                "global": {"read": True, "write": True, "delete": True},
                "mode": "allowlist",
                "deck_permissions": {
                    "allowlist": ["Spanish", "French", "Languages::*"],
                    "denylist": [],
                },
            }
        }
        pm = PermissionManager(config)

        # Listed decks should be allowed
        pm.check_deck_permission("Spanish", PermissionAction.READ)
        pm.check_deck_permission("French", PermissionAction.WRITE)

        # Pattern matching should work
        pm.check_deck_permission("Languages::German", PermissionAction.READ)
        pm.check_deck_permission("Languages::Japanese::Kanji", PermissionAction.WRITE)

        # Unlisted decks should be denied
        with pytest.raises(PermissionError, match="not in the allowlist"):
            pm.check_deck_permission("Personal", PermissionAction.READ)

    def test_denylist_mode(self):
        """Test denylist mode."""
        config = {
            "permissions": {
                "global": {"read": True, "write": True, "delete": True},
                "mode": "denylist",
                "deck_permissions": {
                    "allowlist": [],
                    "denylist": ["Personal::*", "Work::*", "*.Private"],
                },
            }
        }
        pm = PermissionManager(config)

        # Non-denied decks should be allowed
        pm.check_deck_permission("Spanish", PermissionAction.READ)
        pm.check_deck_permission("Study::Public", PermissionAction.WRITE)

        # Denied patterns should be blocked
        with pytest.raises(PermissionError, match="in the denylist"):
            pm.check_deck_permission("Personal::Diary", PermissionAction.READ)

        with pytest.raises(PermissionError, match="in the denylist"):
            pm.check_deck_permission("Work::Confidential", PermissionAction.READ)

        with pytest.raises(PermissionError, match="in the denylist"):
            pm.check_deck_permission("Family.Private", PermissionAction.READ)

    def test_tag_restrictions(self):
        """Test tag-based restrictions."""
        config = {
            "permissions": {
                "global": {"read": True, "write": True, "delete": True},
                "mode": "denylist",
                "tag_restrictions": {
                    "protected_tags": ["important", "exam"],
                    "readonly_tags": ["archive", "reference"],
                },
            }
        }
        pm = PermissionManager(config)

        # Normal tags should allow all operations
        pm.check_tag_permission(["spanish", "vocab"], PermissionAction.READ)
        pm.check_tag_permission(["spanish", "vocab"], PermissionAction.WRITE)
        pm.check_tag_permission(["spanish", "vocab"], PermissionAction.DELETE)

        # Protected tags should only allow read
        pm.check_tag_permission(["important", "spanish"], PermissionAction.READ)
        with pytest.raises(PermissionError, match="protected tags"):
            pm.check_tag_permission(["important", "spanish"], PermissionAction.WRITE)
        with pytest.raises(PermissionError, match="protected tags"):
            pm.check_tag_permission(["exam", "final"], PermissionAction.DELETE)

        # Readonly tags should only allow read
        pm.check_tag_permission(["archive"], PermissionAction.READ)
        with pytest.raises(PermissionError, match="readonly tags"):
            pm.check_tag_permission(["archive"], PermissionAction.WRITE)
        with pytest.raises(PermissionError, match="readonly tags"):
            pm.check_tag_permission(["reference", "book"], PermissionAction.DELETE)

    def test_note_type_permissions(self):
        """Test note type permissions."""
        config = {
            "permissions": {
                "global": {"read": True, "write": True, "delete": True},
                "mode": "denylist",
                "note_type_permissions": {
                    "allow_create": False,
                    "allow_modify": True,
                    "allowed_types": ["Basic", "Cloze"],
                },
            }
        }
        pm = PermissionManager(config)

        # Creating note types should be denied
        with pytest.raises(
            PermissionError, match="Creating new note types is not allowed"
        ):
            pm.check_note_type_permission("NewType", PermissionAction.CREATE)

        # Allowed types should work
        pm.check_note_type_permission("Basic", PermissionAction.WRITE)
        pm.check_note_type_permission("Cloze", PermissionAction.WRITE)

        # Disallowed types should fail
        with pytest.raises(PermissionError, match="not in the allowed types"):
            pm.check_note_type_permission("Image Occlusion", PermissionAction.WRITE)

    def test_filter_decks(self):
        """Test deck filtering."""
        config = {
            "permissions": {
                "mode": "allowlist",
                "deck_permissions": {
                    "allowlist": ["Spanish", "French"],
                },
            }
        }
        pm = PermissionManager(config)

        decks = [
            {"id": 1, "name": "Spanish"},
            {"id": 2, "name": "French"},
            {"id": 3, "name": "German"},
            {"id": 4, "name": "Personal"},
        ]

        filtered = pm.filter_decks(decks)
        assert len(filtered) == 2
        assert filtered[0]["name"] == "Spanish"
        assert filtered[1]["name"] == "French"

    def test_filter_notes(self):
        """Test note filtering."""
        config = {
            "permissions": {
                "tag_restrictions": {
                    "protected_tags": ["private"],
                    "readonly_tags": ["archive"],
                },
            }
        }
        pm = PermissionManager(config)

        notes = [
            {"id": 1, "tags": ["spanish", "vocab"]},
            {"id": 2, "tags": ["private", "personal"]},
            {"id": 3, "tags": ["archive", "old"]},
            {"id": 4, "tags": []},
        ]

        # All notes should be visible (protected/readonly only affects write/delete)
        filtered = pm.filter_notes(notes)
        assert len(filtered) == 4

    def test_pattern_matching(self):
        """Test glob pattern matching."""
        config = {
            "permissions": {
                "mode": "denylist",
                "deck_permissions": {
                    "denylist": ["Personal::*", "*.Private", "Work::*::Confidential"],
                },
            }
        }
        pm = PermissionManager(config)

        # Test exact matches and patterns
        assert pm._matches_any_pattern("Personal::Diary", ["Personal::*"])
        assert pm._matches_any_pattern("Study.Private", ["*.Private"])
        assert pm._matches_any_pattern(
            "Work::Project::Confidential", ["Work::*::Confidential"]
        )
        assert not pm._matches_any_pattern("Spanish", ["Personal::*"])
        assert not pm._matches_any_pattern("Public.Study", ["*.Private"])

    def test_permission_summary(self):
        """Test getting permission summary."""
        config = {
            "permissions": {
                "global": {"read": True, "write": False, "delete": False},
                "mode": "allowlist",
                "deck_permissions": {
                    "allowlist": ["Spanish"],
                    "denylist": ["Personal"],
                },
                "protected_decks": ["Default"],
                "tag_restrictions": {
                    "protected_tags": ["exam"],
                    "readonly_tags": ["archive"],
                },
                "note_type_permissions": {
                    "allow_create": True,
                    "allowed_types": ["Basic"],
                },
            }
        }
        pm = PermissionManager(config)

        summary = pm.get_permission_summary()
        assert summary["mode"] == "allowlist"
        assert summary["global_permissions"]["read"] is True
        assert summary["global_permissions"]["write"] is False
        assert "Default" in summary["protected_decks"]
        assert "Spanish" in summary["deck_allowlist"]
        assert "exam" in summary["protected_tags"]
        assert "Basic" in summary["note_type_permissions"]["allowed_types"]
