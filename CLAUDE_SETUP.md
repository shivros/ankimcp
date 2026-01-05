# Setting up AnkiMCP with Claude Code

AnkiMCP is an Anki addon that exposes your Anki data via the Model Context Protocol (MCP). When Anki is running, it provides an HTTP server with SSE transport that MCP clients can connect to directly.

## Step 1: Install the Anki addon

1. Copy the `ankimcp` folder to your Anki addons directory:
   - **macOS**: `~/Library/Application Support/Anki2/addons21/`
   - **Linux**: `~/.local/share/Anki2/addons21/`
   - **Windows**: `%APPDATA%\Anki2\addons21\`

2. Restart Anki and open your profile
3. The MCP server starts automatically on `localhost:4473`

## Step 2: Configure your MCP client

AnkiMCP exposes an SSE endpoint that MCP clients can connect to directly.

### For Claude Desktop

Edit `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ankimcp": {
      "url": "http://localhost:4473/sse"
    }
  }
}
```

### For other MCP clients

Point the client to the SSE endpoint: `http://localhost:4473/sse`

## Step 3: Restart your MCP client

1. Completely quit the client (not just close the window)
2. Start the client again
3. Make sure Anki is running with your profile open

## Available Endpoints

When Anki is running:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sse` | GET | SSE transport (MCP standard) |
| `/messages?session_id=X` | POST | Send messages to SSE session |
| `/mcp` | POST | Direct JSON-RPC (stateless) |
| `/health` | GET | Health check |

## Testing the Connection

You can test if the server is running:

```bash
# Health check
curl http://localhost:4473/health

# List tools via direct JSON-RPC
curl -X POST http://localhost:4473/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## How it works

1. **Anki addon** runs an HTTP server on port 4473 when Anki is open
2. **MCP clients** connect directly to the SSE endpoint
3. The server speaks native MCP protocol (JSON-RPC 2.0 over SSE)

## Configuration

The addon can be configured via Anki's addon config (Tools → Add-ons → AnkiMCP → Config):

- `host`: Server host (default: "localhost")
- `port`: Server port (default: 4473)

Or via environment variables:
- `ANKIMCP_HOST`
- `ANKIMCP_PORT`

## Troubleshooting

- **"Cannot connect"**: Make sure Anki is running and you've opened a profile
- **Tools not showing**: Restart your MCP client completely
- **Port conflict**: Change the port in addon config
