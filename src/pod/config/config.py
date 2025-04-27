from pathlib import Path

# Constants
CONFIG_DIR = Path.home() / ".pod"
DOWNLOADS_DIR = CONFIG_DIR / "downloads"
DATABASE_FILE = CONFIG_DIR / "database.json"

# Ensure directories exist
if not CONFIG_DIR.exists():
    CONFIG_DIR.mkdir()
if not DOWNLOADS_DIR.exists():
    DOWNLOADS_DIR.mkdir()
