from textual.app import  ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button, Static, Label, Input
)

from src.pod.services.feedupdater import FeedUpdater
from src.pod.widgets.feedslist import FeedsList

class AddFeedDialog(Static):
    """Dialog for adding a new feed."""

    def __init__(self, feed_updater: FeedUpdater):
        super().__init__()
        self.feed_updater = feed_updater

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Add Podcast Feed", classes="dialog-title"),
            Input(placeholder="Enter podcast RSS feed URL", id="feed-url-input"),
            Horizontal(
                Button("Cancel", id="cancel-add-feed", variant="default"),
                Button("Add", id="confirm-add-feed", variant="primary"),
                id="dialog-buttons"
            ),
            id="add-feed-dialog"
        )

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "cancel-add-feed":
            self.remove()
        elif event.button.id == "confirm-add-feed":
            self._add_feed()

    def _add_feed(self):
        """Add a new feed from the entered URL."""
        url_input = self.query_one("#feed-url-input", Input)
        url = url_input.value.strip()

        if not url:
            # Show error
            url_input.border_title = "Please enter a URL"
            return

        # Show loading state
        url_input.disabled = True
        confirm_button = self.query_one("#confirm-add-feed", Button)
        confirm_button.label = "Adding..."
        confirm_button.disabled = True

        # Add feed in a worker thread
        # def do_add_feed():
        #     feed = self.feed_updater.add_feed_from_url(url)
        #     self.call_from_thread(self._update_after_add, feed)

        # import threading
        # thread = threading.Thread(target=do_add_feed)
        # thread.daemon = True
        # thread.start()

    def _update_after_add(self, feed):
        """Update UI after feed is added."""
        if feed:
            # Success - close dialog and refresh feeds list
            feeds_list = self.app.query_one(FeedsList)
            feeds_list.load_feeds()
            self.remove()
        else:
            # Error
            url_input = self.query_one("#feed-url-input", Input)
            url_input.disabled = False
            url_input.border_title = "Invalid feed URL"

            confirm_button = self.query_one("#confirm-add-feed", Button)
            confirm_button.label = "Add"
            confirm_button.disabled = False
