# AnkiMCP Configuration

Configure the MCP server that exposes your Anki data to AI assistants.

## Server Settings

- **host**: The hostname to bind the server to (default: `localhost`)
- **port**: The port number for the HTTP server (default: `4473`)

## Permissions

Control what AI assistants can do with your Anki data.

### Global Permissions

- **read**: Allow reading decks, notes, and cards (default: `true`)
- **write**: Allow creating and modifying notes/cards (default: `true`)
- **delete**: Allow deleting notes/cards (default: `true`)

### Mode

- **mode**: Permission filtering mode
  - `allowlist`: Only allow access to decks in the allowlist
  - `denylist`: Allow access to all decks except those in the denylist

### Deck Permissions

- **deck_permissions.allowlist**: List of deck names to allow (when mode is `allowlist`)
- **deck_permissions.denylist**: List of deck names to deny (when mode is `denylist`)
- **protected_decks**: Decks that cannot be deleted (default: `["Default"]`)

### Tag Restrictions

- **tag_restrictions.protected_tags**: Tags that prevent notes from being modified
- **tag_restrictions.readonly_tags**: Tags that make notes read-only

### Note Type Permissions

- **note_type_permissions.allow_create**: Allow creating new note types (default: `true`)
- **note_type_permissions.allow_modify**: Allow modifying existing note types (default: `false`)
- **note_type_permissions.allowed_types**: List of note type names to allow (empty = all)
