# AnkiMCP

[![CI](https://github.com/matt-fff/ankimcp/actions/workflows/ci.yml/badge.svg)](https://github.com/matt-fff/ankimcp/actions/workflows/ci.yml)
[![Test Matrix](https://github.com/matt-fff/ankimcp/actions/workflows/test-matrix.yml/badge.svg)](https://github.com/matt-fff/ankimcp/actions/workflows/test-matrix.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Integrate your Anki decks with your choice of AI through the Model Context Protocol (MCP).

AnkiMCP is an Anki addon that exposes your Anki collection data (decks, notes, cards, and review statistics) via an MCP server, allowing AI assistants to help you study, create cards, and analyze your learning progress.

## Features

- List all available decks with card counts
- Search notes using Anki's powerful search syntax
- Get detailed information about specific notes and cards
- View review statistics for decks or your entire collection
- Access card scheduling information and review history
- Create, update, and delete notes and decks
- Comprehensive permission system to control AI access
- Protect sensitive decks and notes from modification

## Installation

### As an Anki Addon

1. Download the addon from AnkiWeb or clone this repository
2. Copy the `src/ankimcp` folder to your Anki addons directory (or run
   `./install_addon.sh` to copy files and vendor the `mcp` dependency)
3. Restart Anki
4. The MCP server will start automatically when you open your profile

### Packaging for AnkiWeb

Use the helper script to generate a distributable `.ankiaddon` archive that
matches the [AnkiWeb sharing requirements](https://addon-docs.ankiweb.net/sharing.html):

```bash
python package_for_ankiweb.py --version 1.0.0
```

The resulting file is written to the `dist/` directory (e.g.
`dist/ankimcp-1.0.0-YYYYmmdd-HHMMSS.ankiaddon`). The script reads metadata from
`src/ankimcp/manifest.json`, vendors the `mcp` runtime dependency into
`vendor/`, and filters out common build artifacts so the archive is ready to
upload to AnkiWeb. Use `--skip-deps` if you are packaging an already vendored
source tree.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ankimcp.git
cd ankimcp

# Install dependencies with Rye
rye sync

# Run the test server (with mock data)
rye run python -m ankimcp
```

## Usage

Once installed, the MCP server runs automatically when Anki is open. You can then connect to it from any MCP-compatible AI assistant.

### Available MCP Tools

- `list_decks` - List all available Anki decks
- `get_deck_info` - Get detailed information about a specific deck
- `search_notes` - Search for notes using Anki's search syntax
- `get_note` - Get detailed information about a specific note
- `get_cards_for_note` - Get all cards associated with a note
- `get_review_stats` - Get review statistics for a deck or overall
- `create_deck` - Create a new deck
- `create_note_type` - Create a new note type (card template)
- `create_note` - Create a new note in a deck
- `update_note` - Update an existing note's fields or tags
- `delete_note` - Delete a note and all its cards
- `get_permissions` - View current permission settings

## Permissions

AnkiMCP includes a comprehensive permission system to control AI access to your collection. You can:

- Set global read/write/delete permissions
- Use allowlists or denylists for deck access
- Protect specific decks from modification
- Restrict access based on note tags
- Control which note types can be created

See [PERMISSIONS.md](PERMISSIONS.md) for detailed configuration options.

## Configuration

Edit the addon configuration in Anki (Tools → Add-ons → AnkiMCP → Config):

```json
{
    "host": "localhost",
    "port": 4473,
    "permissions": {
        "global": {
            "read": true,
            "write": true,
            "delete": false
        },
        "mode": "denylist",
        "deck_permissions": {
            "denylist": ["Personal::*"]
        },
        "protected_decks": ["Default"]
    }
}
```

## Testing & Acceptance

- Run `rye run test` to exercise the automated suite.
- COD-73 acceptance: packaged add-on bundles the `mcp` runtime dependency (via `package_for_ankiweb.py` or `install_addon.sh`) and the automated tests pass.

## More Information

Visit https://ankimcp.com for more details and documentation.
