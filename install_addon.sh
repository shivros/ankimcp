#!/bin/bash
# Script to install AnkiMCP as a local Anki addon

# Find Anki's addon directory
if [ -d "$HOME/.local/share/Anki2/addons21" ]; then
    # Linux
    ADDON_DIR="$HOME/.local/share/Anki2/addons21"
elif [ -d "$HOME/Library/Application Support/Anki2/addons21" ]; then
    # macOS
    ADDON_DIR="$HOME/Library/Application Support/Anki2/addons21"
elif [ -d "$APPDATA/Anki2/addons21" ]; then
    # Windows (in WSL/Git Bash)
    ADDON_DIR="$APPDATA/Anki2/addons21"
else
    echo "Error: Could not find Anki addons directory"
    echo "Please ensure Anki is installed"
    exit 1
fi

# Create addon directory
ANKIMCP_DIR="$ADDON_DIR/ankimcp"
echo "Installing AnkiMCP to: $ANKIMCP_DIR"

# Remove old installation if exists
if [ -d "$ANKIMCP_DIR" ]; then
    echo "Removing existing installation..."
    rm -rf "$ANKIMCP_DIR"
fi

# Create directory
mkdir -p "$ANKIMCP_DIR"

# Copy addon files
echo "Copying addon files..."
cp -r src/ankimcp/* "$ANKIMCP_DIR/"

# Create meta.json for Anki
cat > "$ANKIMCP_DIR/meta.json" << EOF
{
    "name": "AnkiMCP",
    "mod": $(date +%s),
    "config": {
        "host": "localhost",
        "port": 4473
    }
}
EOF

echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Restart Anki"
echo "2. The MCP server will start automatically when you open your profile"
echo "3. Configure your AI assistant to connect to localhost:4473"
echo ""
echo "To configure the addon in Anki:"
echo "Tools → Add-ons → AnkiMCP → Config"