"""Run the AnkiMCP client that connects to the running Anki server."""

import asyncio

from .client import main

if __name__ == "__main__":
    print("Starting AnkiMCP client...")
    print("This client connects to the Anki MCP server running on localhost:4473")
    print("Make sure Anki is running with the AnkiMCP addon installed.")
    asyncio.run(main())
