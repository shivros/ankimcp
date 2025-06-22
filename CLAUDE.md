# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

AnkiMCP is an Anki addon that exposes Anki collection data via a Model Context Protocol (MCP) server. This allows AI assistants to interact with Anki decks, notes, cards, and review statistics.

## Development Environment

- **Python Version**: 3.12.9 (specified in `.python-version`)
- **Package Manager**: Rye
- **Build System**: Hatchling
- **Package Structure**: Uses modern `src/` layout
- **Key Dependencies**: `mcp` (MCP SDK), `anki` (Anki Python library)

## Common Commands

### Dependency Management
```bash
# Install dependencies
rye sync

# Add a new dependency
rye add <package>

# Add a development dependency
rye add --dev <package>

# Update dependencies
rye lock --update-all
```

### Development
```bash
# Run the test server with mock data
rye run python -m ankimcp

# Install in editable mode for development
rye sync
```

### Testing
```bash
# Run tests (after test framework is added)
rye run pytest

# Run tests with coverage
rye run pytest --cov=ankimcp
```

### Linting and Formatting
```bash
# Format code
rye run black src/

# Lint code
rye run ruff check src/

# Type checking
rye run mypy src/
```

## Project Structure

```
src/ankimcp/
├── __init__.py          # Anki addon entry point with hooks
├── __main__.py          # Standalone test server with mock data
├── server.py            # MCP server implementation
├── anki_interface.py    # Abstraction layer for Anki operations
├── addon_config.json    # Anki addon configuration
└── manifest.json        # Anki addon metadata
```

## Architecture

The addon follows a layered architecture:

1. **Anki Integration Layer** (`__init__.py`)
   - Registers Anki hooks to start/stop the MCP server
   - Manages server lifecycle with profile open/close

2. **MCP Server** (`server.py`)
   - Implements MCP protocol endpoints
   - Defines available tools for AI interaction
   - Handles tool execution and response formatting

3. **Anki Interface** (`anki_interface.py`)
   - Provides abstraction over Anki's API
   - Implements data access methods
   - Handles conversion between Anki objects and JSON

4. **Test Infrastructure** (`__main__.py`)
   - Mock implementation for testing without Anki
   - Allows standalone server testing

## Available MCP Tools

- `list_decks`: Returns all decks with card counts
- `get_deck_info`: Detailed deck statistics
- `search_notes`: Search using Anki's query syntax
- `get_note`: Full note data with fields
- `get_cards_for_note`: All cards for a specific note
- `get_review_stats`: Review statistics for deck or collection

## Installation as Anki Addon

To install in Anki:
1. Copy `src/ankimcp/` to Anki's addons directory
2. Restart Anki
3. Server starts automatically on profile load

## Key Implementation Details

- Server runs as subprocess to avoid blocking Anki UI
- Uses stdio for MCP communication
- Gracefully handles Anki availability (addon vs standalone)
- Configuration via Anki's addon config system