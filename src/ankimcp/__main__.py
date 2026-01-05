"""AnkiMCP - Anki addon that exposes MCP endpoints.

This module prints usage information. The actual MCP server runs inside Anki.
"""

import os

ANKIMCP_HOST = os.environ.get("ANKIMCP_HOST", "localhost")
ANKIMCP_PORT = os.environ.get("ANKIMCP_PORT", "4473")


def main():
    """Print usage information."""
    base_url = f"http://{ANKIMCP_HOST}:{ANKIMCP_PORT}"

    print("AnkiMCP - Model Context Protocol server for Anki")
    print("=" * 50)
    print()
    print("This is an Anki addon. The MCP server runs inside Anki automatically")
    print("when you open your profile.")
    print()
    print("INSTALLATION:")
    print("  1. Copy the ankimcp folder to your Anki addons directory")
    print("  2. Restart Anki and open a profile")
    print("  3. The MCP server starts automatically")
    print()
    print("ENDPOINTS (when Anki is running):")
    print(f"  SSE transport:    {base_url}/sse")
    print(f"  Messages:         {base_url}/messages")
    print(f"  Direct JSON-RPC:  {base_url}/mcp")
    print(f"  Health check:     {base_url}/health")
    print()
    print("MCP CLIENT CONFIGURATION:")
    print("  Point your MCP client to the SSE endpoint:")
    print(f"    {base_url}/sse")
    print()
    print("ENVIRONMENT VARIABLES:")
    print("  ANKIMCP_HOST  - Server host (default: localhost)")
    print("  ANKIMCP_PORT  - Server port (default: 4473)")
    print()
    print("For more information, see the README.")


if __name__ == "__main__":
    main()
