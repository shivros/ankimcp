"""Permission management for AnkiMCP."""

import fnmatch
import logging
from enum import Enum
from typing import Dict, List

logger = logging.getLogger(__name__)


class PermissionAction(Enum):
    """Types of actions that can be performed."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"


class PermissionMode(Enum):
    """Permission evaluation modes."""

    ALLOWLIST = "allowlist"  # Only listed items are allowed
    DENYLIST = "denylist"  # All items allowed except those listed


class PermissionError(Exception):
    """Raised when a permission check fails."""

    pass


class PermissionManager:
    """Manages permissions for AnkiMCP operations."""

    def __init__(self, config: Dict):
        """Initialize with permission configuration."""
        self.config = config.get("permissions", {})
        self.global_perms = self.config.get("global", {})
        self.mode = PermissionMode(self.config.get("mode", "allowlist"))
        self.deck_permissions = self.config.get("deck_permissions", {})
        self.protected_decks = set(self.config.get("protected_decks", ["Default"]))
        self.tag_restrictions = self.config.get("tag_restrictions", {})
        self.note_type_permissions = self.config.get("note_type_permissions", {})

    def check_deck_permission(self, deck_name: str, action: PermissionAction) -> None:
        """Check if an action is allowed on a deck.

        Raises:
            PermissionError: If the action is not allowed
        """
        # Map CREATE to WRITE for global permission check
        global_action = (
            PermissionAction.WRITE if action == PermissionAction.CREATE else action
        )

        # Check global permissions first
        if not self.global_perms.get(global_action.value, True):
            raise PermissionError(
                f"Global {global_action.value} permission denied for all decks"
            )

        # Check if deck is protected (CREATE is treated as modification for protected decks)
        if deck_name in self.protected_decks and action in [
            PermissionAction.WRITE,
            PermissionAction.DELETE,
            PermissionAction.CREATE,
        ]:
            raise PermissionError(f"Deck '{deck_name}' is protected from modifications")

        # Check allowlist/denylist
        allowlist = self.deck_permissions.get("allowlist", [])
        denylist = self.deck_permissions.get("denylist", [])

        if self.mode == PermissionMode.ALLOWLIST:
            # In allowlist mode, deck must be explicitly allowed
            if allowlist and not self._matches_any_pattern(deck_name, allowlist):
                raise PermissionError(
                    f"Deck '{deck_name}' is not in the allowlist for {action.value}"
                )
        else:
            # In denylist mode, deck must not be explicitly denied
            if self._matches_any_pattern(deck_name, denylist):
                raise PermissionError(
                    f"Deck '{deck_name}' is in the denylist for {action.value}"
                )

    def check_tag_permission(self, tags: List[str], action: PermissionAction) -> None:
        """Check if an action is allowed for notes with given tags.

        Raises:
            PermissionError: If the action is not allowed
        """
        protected_tags = set(self.tag_restrictions.get("protected_tags", []))
        readonly_tags = set(self.tag_restrictions.get("readonly_tags", []))

        tag_set = set(tags)

        # Check protected tags (no modifications allowed)
        if protected_tags & tag_set and action in [
            PermissionAction.WRITE,
            PermissionAction.DELETE,
        ]:
            protected = protected_tags & tag_set
            raise PermissionError(
                f"Notes with protected tags {protected} cannot be modified"
            )

        # Check readonly tags (only read allowed)
        if readonly_tags & tag_set and action != PermissionAction.READ:
            readonly = readonly_tags & tag_set
            raise PermissionError(
                f"Notes with readonly tags {readonly} cannot be modified"
            )

    def check_note_type_permission(
        self, note_type: str, action: PermissionAction
    ) -> None:
        """Check if an action is allowed for a note type.

        Raises:
            PermissionError: If the action is not allowed
        """
        if action == PermissionAction.CREATE:
            if not self.note_type_permissions.get("allow_create", True):
                raise PermissionError("Creating new note types is not allowed")

        elif action == PermissionAction.WRITE:
            if not self.note_type_permissions.get("allow_modify", True):
                raise PermissionError("Modifying note types is not allowed")

        # Check allowed types restriction
        allowed_types = self.note_type_permissions.get("allowed_types", [])
        if allowed_types and note_type not in allowed_types:
            raise PermissionError(
                f"Note type '{note_type}' is not in the allowed types list"
            )

    def filter_decks(self, decks: List[Dict]) -> List[Dict]:
        """Filter deck list based on read permissions."""
        filtered = []
        for deck in decks:
            try:
                self.check_deck_permission(deck["name"], PermissionAction.READ)
                filtered.append(deck)
            except PermissionError:
                logger.debug(f"Filtering out deck '{deck['name']}' due to permissions")
                continue
        return filtered

    def filter_notes(self, notes: List[Dict]) -> List[Dict]:
        """Filter note list based on tag permissions."""
        filtered = []
        for note in notes:
            try:
                self.check_tag_permission(note.get("tags", []), PermissionAction.READ)
                filtered.append(note)
            except PermissionError:
                logger.debug(f"Filtering out note {note['id']} due to tag permissions")
                continue
        return filtered

    def _matches_any_pattern(self, name: str, patterns: List[str]) -> bool:
        """Check if name matches any of the glob patterns."""
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def get_permission_summary(self) -> Dict:
        """Get a summary of current permissions for display."""
        return {
            "mode": self.mode.value,
            "global_permissions": self.global_perms,
            "protected_decks": list(self.protected_decks),
            "deck_allowlist": self.deck_permissions.get("allowlist", []),
            "deck_denylist": self.deck_permissions.get("denylist", []),
            "protected_tags": self.tag_restrictions.get("protected_tags", []),
            "readonly_tags": self.tag_restrictions.get("readonly_tags", []),
            "note_type_permissions": self.note_type_permissions,
        }
