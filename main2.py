import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
import vlc
from vlc import Instance
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.widgets import (
    Button, Footer, Header, Static, Tree, Label,
    ProgressBar, Input, ContentSwitcher, TabPane, Tabs
)
from textual.widgets.tree import TreeNode
from textual.reactive import reactive

from rss import PodcastRSSParser
from app import PodcastTUIApp

# Constants
CONFIG_DIR = Path.home() / ".podcast_tui"
DOWNLOADS_DIR = CONFIG_DIR / "downloads"
DATABASE_FILE = CONFIG_DIR / "database.json"

# Ensure directories exist
CONFIG_DIR.mkdir(exist_ok=True)
DOWNLOADS_DIR.mkdir(exist_ok=True)

def main():
    app = PodcastTUIApp()
    app.run()

if __name__ == "__main__":
    main()
