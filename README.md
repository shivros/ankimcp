# AnkiMCP

[![CI](https://github.com/matt-fff/ankimcp/actions/workflows/ci.yml/badge.svg)](https://github.com/matt-fff/ankimcp/actions/workflows/ci.yml)
[![Test Matrix](https://github.com/matt-fff/ankimcp/actions/workflows/test-matrix.yml/badge.svg)](https://github.com/matt-fff/ankimcp/actions/workflows/test-matrix.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
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

## Installation

### As an Anki Addon

1. Download the addon from AnkiWeb or clone this repository
2. Copy the `src/ankimcp` folder to your Anki addons directory
3. Restart Anki
4. The MCP server will start automatically when you open your profile

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

## Configuration

Edit the addon configuration in Anki (Tools → Add-ons → AnkiMCP → Config):

```json
{
    "host": "localhost",
    "port": 4473
}
```

## More Information

Visit https://ankimcp.com for more details and documentation.
