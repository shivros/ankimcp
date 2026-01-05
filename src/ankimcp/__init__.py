"""AnkiMCP - Expose Anki data via Model Context Protocol."""

import logging
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global server process
server_process: Optional[subprocess.Popen] = None
server_thread: Optional[threading.Thread] = None


def _add_vendor_site_packages():
    """Add vendored dependencies (e.g., mcp) to sys.path when packaged for Anki."""
    addon_dir = Path(__file__).parent
    vendor_dir = addon_dir / "vendor"

    if vendor_dir.exists():
        vendor_path = str(vendor_dir)
        if vendor_path not in sys.path:
            sys.path.insert(0, vendor_path)
            logger.debug(f"Added vendor path to sys.path: {vendor_path}")


_add_vendor_site_packages()


def start_mcp_server():
    """Start the MCP server in a separate process."""
    global server_process

    try:
        # When running as Anki addon
        from aqt import mw  # type: ignore
        from aqt.utils import showInfo  # type: ignore

        if not mw or not mw.col:
            logger.error("Anki collection not available")
            return

        # Read configuration (addon config takes priority, then env vars, then defaults)
        config = mw.addonManager.getConfig(__name__)
        default_host = os.environ.get("ANKIMCP_HOST", "localhost")
        default_port = int(os.environ.get("ANKIMCP_PORT", "4473"))
        host = config.get("host", default_host) if config else default_host
        port = config.get("port", default_port) if config else default_port

        # Start the server process
        addon_dir = Path(__file__).parent
        server_script = addon_dir / "run_server.py"

        # Start the server directly in this process
        from .anki_interface import AnkiInterface
        from .simple_http_server import SimpleHTTPServer

        # Create Anki interface with permission configuration
        anki_interface = AnkiInterface(mw.col, config)

        # Create and start HTTP server
        http_server = SimpleHTTPServer(anki_interface, host, port)
        http_server.start()

        # Store the server in the addon manager's config
        # so we can stop it later
        if not hasattr(mw.addonManager, "_ankimcp_server"):
            setattr(mw.addonManager, "_ankimcp_server", http_server)

        logger.info(f"MCP server started on {host}:{port}")

    except ImportError as e:
        # Log the actual import error for debugging
        logger.error(f"Import error while starting MCP server: {e}")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        if "showInfo" in locals():
            showInfo(f"Failed to start AnkiMCP server: {e}")


def stop_mcp_server():
    """Stop the MCP server."""
    try:
        from aqt import mw

        if hasattr(mw.addonManager, "_ankimcp_server"):
            server = getattr(mw.addonManager, "_ankimcp_server")
            server.stop()
            delattr(mw.addonManager, "_ankimcp_server")
            logger.info("MCP server stopped")
    except Exception as e:
        logger.error(f"Error stopping server: {e}")


# Anki addon hooks
try:
    from aqt import gui_hooks  # type: ignore

    def on_profile_loaded():
        """Start the server when Anki profile is loaded."""
        start_mcp_server()

    def on_profile_will_close():
        """Stop the server when Anki profile is closing."""
        stop_mcp_server()

    # Register hooks
    gui_hooks.profile_did_open.append(on_profile_loaded)
    gui_hooks.profile_will_close.append(on_profile_will_close)

except ImportError:
    # Not running as Anki addon
    pass
