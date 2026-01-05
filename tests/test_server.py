"""Tests for the MCP server."""

import pytest

from ankimcp.server import list_tools


@pytest.mark.asyncio
async def test_list_tools():
    """Test that list_tools returns expected tools."""
    tools = await list_tools()

    # Check we have the expected number of tools
    assert len(tools) == 15

    # Check tool names
    tool_names = {tool.name for tool in tools}
    expected_names = {
        "get_permissions",
        "list_decks",
        "get_deck_info",
        "search_notes",
        "get_note",
        "get_cards_for_note",
        "get_review_stats",
        "list_note_types",
        "create_deck",
        "create_note_type",
        "create_note",
        "update_note",
        "delete_note",
        "delete_deck",
        "update_deck",
    }
    assert tool_names == expected_names

    # Check each tool has required fields
    for tool in tools:
        assert tool.name
        assert tool.description
        assert tool.inputSchema
