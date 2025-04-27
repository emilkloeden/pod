from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button, Static, Tree, Label
)

from src.pod.services.databasemanager import PodcastDatabase

class FeedsList(Static):
    """Widget showing list of subscribed feeds."""

    def __init__(self, database: PodcastDatabase):
        super().__init__()
        self.database = database
        print(f"\n\n\n{self.database=}")

    def compose(self) -> ComposeResult:
        yield Container(
            Label("My Podcasts", classes="section-title"),
            Tree("Subscriptions", id="feeds-tree"),
            # Button("Add Feed", id="add-feed-button"),
            id="feeds-container"
        )

    def on_mount(self):
        """Load feeds when mounted."""

        with open("feedlist.txt", "w") as f:
            f.write("FeedsList mounted")
            tree = self.query_one("#feeds-tree", Tree)
            f.write(f"Tree widget found: {tree}")
            tree.styles.min_height = 10

        self.load_feeds()

    def load_feeds(self):
        """Load feeds into the tree."""
        tree = self.query_one("#feeds-tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()

        # More detailed debug info
        with open("feeds.txt", "w") as f:
            f.write(f"Database: {self.database}")
            f.write(f"Feeds: {self.database.feeds}")
            for feed in self.database.feeds:
                f.write(f"Feed: {feed.id} - {feed.title}")
                node = root.add(feed.title, {"id": feed.id, "type": "feed"})
                # Make the node expanded by default
                node.expand()
                # Maybe add a child node to see if that helps with visibility
                node.add("(Click to view episodes)")

        # Debug print
            f.write(f"Loading feeds: {len(self.database.feeds)} found")

        feeds = self.database.feeds
        if not feeds:
            root.add("No podcasts yet. Click 'Add Feed' to get started.")
            return

        for feed in feeds:
            node = root.add(feed.title, {"id": feed.id, "type": "feed"})# We could add episode nodes here, but let's keep it simple for now

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        """Handle feed selection."""
        if event.node.data:
            node_data = event.node.data
            if node_data.get("type") == "feed":
                feed_id = node_data.get("id")
                # COMMENTED WHILST DEBUGGING
                # self.app.show_feed(feed_id)
