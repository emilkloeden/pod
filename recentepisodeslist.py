from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.widgets import (
    Button, Footer, Header, Static, Tree, Label,
    ProgressBar, Input, ContentSwitcher, TabPane, Tabs
)
from databasemanager import PodcastDatabase

class RecentEpisodesList(Static):
    """Widget showing recently published episodes."""

    def __init__(self, database: PodcastDatabase):
        super().__init__()
        self.database = database

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Recent Episodes", classes="section-title"),
            Static(id="episodes-list"),
            id="recent-episodes"
        )

    def on_mount(self):
        """Load episodes when mounted."""
        self.load_episodes()

    def load_episodes(self):
        """Load recent episodes."""
        episodes_container = self.query_one("#episodes-list", Static)
        episodes_container.remove_children()

        recent_episodes = self.database.get_recent_episodes(limit=10)

        for episode in recent_episodes:
            feed = self.database.get_feed(episode.feed_id)
            feed_name = feed.title if feed else "Unknown"

            episode_container = Horizontal(
                Label(f"{episode.title}", classes="episode-title"),
                Label(f"({feed_name})", classes="feed-name"),
                Label(episode.format_duration(), classes="episode-duration"),
                Button("▶", classes="play-button"),
                classes="episode-item",
                id=f"episode-{episode.guid}"
            )

            episodes_container.mount(episode_container)
