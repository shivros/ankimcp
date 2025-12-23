# Installing AnkiMCP as a Local Anki Addon

## Method 1: Using the Install Script (Recommended)

Simply run the provided install script:

```bash
./install_addon.sh
```

This will automatically:
- Find your Anki addons directory
- Copy the addon files
- Vendor the `mcp` runtime dependency into `vendor/`
- Create the necessary configuration

## Method 2: Manual Installation

1. **Find your Anki addons directory:**
   - **Linux**: `~/.local/share/Anki2/addons21/`
   - **macOS**: `~/Library/Application Support/Anki2/addons21/`
   - **Windows**: `%APPDATA%\Anki2\addons21\`

2. **Create the addon folder:**
   ```bash
   mkdir -p [ANKI_ADDONS_DIR]/ankimcp
   ```

3. **Copy the addon files:**
   ```bash
   cp -r src/ankimcp/* [ANKI_ADDONS_DIR]/ankimcp/
   ```

4. **Install runtime dependencies into the addon folder:**
   ```bash
   python -m pip install --upgrade --target [ANKI_ADDONS_DIR]/ankimcp/vendor "mcp>=1.9.4"
   ```

5. **Create meta.json:**
   Create a file `[ANKI_ADDONS_DIR]/ankimcp/meta.json` with:
   ```json
   {
       "name": "AnkiMCP",
       "mod": 0,
       "config": {
           "host": "localhost",
           "port": 4473
       }
   }
   ```

## Method 3: Symlink for Development

For active development, you can create a symlink instead of copying files:

```bash
# Linux/macOS
ln -s $(pwd)/src/ankimcp ~/.local/share/Anki2/addons21/ankimcp

# You'll still need to create meta.json in the source directory
cp meta.json src/ankimcp/
```

## After Installation

1. **Restart Anki** - The addon won't load until Anki is restarted
2. **Check the addon loaded** - Go to Tools → Add-ons and verify AnkiMCP is listed
3. **Configure if needed** - Select AnkiMCP and click Config to change host/port
4. **Verify it's running** - You should see a notification when opening your profile

## Troubleshooting

- **Addon not showing up**: Make sure you copied to the correct addons21 directory
- **Server not starting**: Check Tools → Add-ons → View Files for error logs
- **Port conflict**: Change the port in the addon configuration

## Connecting Your AI Assistant

Once installed, configure your AI assistant to use the MCP server at:
- **Host**: localhost
- **Port**: 4473 (default)

The server provides tools for:
- Listing decks
- Searching notes
- Getting card details
- Viewing review statistics
