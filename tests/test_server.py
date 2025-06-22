"""Tests for the MCP server."""

import pytest

from ankimcp.server import list_tools


@pytest.mark.asyncio
async def test_list_tools():
    """Test that list_tools returns expected tools."""
    tools = await list_tools()

    # Check we have the expected number of tools
    assert len(tools) == 6

    # Check tool names
    tool_names = {tool.name for tool in tools}
    expected_names = {
        "list_decks",
        "get_deck_info",
        "search_notes",
        "get_note",
        "get_cards_for_note",
        "get_review_stats",
    }
    assert tool_names == expected_names

    # Check each tool has required fields
    for tool in tools:
        assert tool.name
        assert tool.description
        assert tool.inputSchema
