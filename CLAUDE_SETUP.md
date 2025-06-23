# Setting up AnkiMCP with Claude Code

AnkiMCP works by running an HTTP server inside Anki, and Claude Code connects to it via a client that translates between MCP stdio and HTTP.

## Step 1: Find your Claude Code configuration file

The configuration file is located at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## Step 2: Add AnkiMCP to the configuration

Edit the `claude_desktop_config.json` file and add the AnkiMCP server configuration:

```json
{
  "mcpServers": {
    "ankimcp": {
      "command": "python",
      "args": [
        "-m",
        "ankimcp"
      ],
      "cwd": "/home/matt/Workspaces/matt-fff/ankimcp",
      "env": {
        "PYTHONPATH": "/home/matt/Workspaces/matt-fff/ankimcp/src"
      }
    }
  }
}
```

**Important**: Replace `/home/matt/Workspaces/matt-fff/ankimcp` with the actual path to your ankimcp directory.

## Step 3: Make sure dependencies are available

Install the package dependencies:

```bash
cd /path/to/ankimcp
rye sync
```

## Step 4: Restart Claude Code

After editing the configuration:
1. Completely quit Claude Code (not just close the window)
2. Start Claude Code again
3. You should see AnkiMCP in the MCP servers list

## Step 5: Make sure Anki is running

1. Start Anki
2. Open your profile
3. You should see a notification that the AnkiMCP server started
4. The server runs on `localhost:4473`

## Step 6: Test the connection

In Claude Code, you can test if the connection is working:
- Ask: "Check if Anki is running" (uses the `anki_status` tool)
- Ask: "List my Anki decks"
- Ask: "Search for notes in my Anki collection"

## How it works

1. **Anki addon** runs an HTTP server on port 4473 when Anki is open
2. **Claude Code** runs the AnkiMCP client via stdio
3. **The client** translates MCP commands to HTTP requests to the Anki server
4. This allows Claude to access your real Anki data while Anki is running

## Troubleshooting

- **"Cannot connect to Anki"**: Make sure Anki is running and you've opened a profile
- **Tools not showing**: Restart Claude Code completely
- **Server not starting**: Check the Anki addon (Tools → Add-ons → View Files) for errors
