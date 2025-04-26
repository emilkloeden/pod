from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    Button, Static, Tree, Label
)

from src.pod.services.databasemanager import PodcastDatabase

class FeedsList(Static):
    """Widget showing list of subscribed feeds."""

    def __init__(self, database: PodcastDatabase):
        super().__init__()
        self.database = database

    def compose(self) -> ComposeResult:
        yield Container(
            Label("My Podcasts", classes="section-title"),
            Tree("Subscriptions", id="feeds-tree"),
            Button("Add Feed", id="add-feed-button"),
            id="feeds-container"
        )

    def on_mount(self):
        """Load feeds when mounted."""
        self.load_feeds()

    def load_feeds(self):
        """Load feeds into the tree."""
        tree = self.query_one("#feeds-tree", Tree)
        tree.clear()

        root = tree.root
        root.expand()

        for feed in self.database.feeds:
            node = root.add(feed.title, {"id": feed.id, "type": "feed"})
            # We could add episode nodes here, but let's keep it simple for now

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        """Handle feed selection."""
        if event.node.data:
            node_data = event.node.data
            if node_data.get("type") == "feed":
                feed_id = node_data.get("id")
                self.app.show_feed(feed_id)
