from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (Button, Static, Label, Input)

from textual.reactive import reactive
import httpx
import asyncio


class DiscoverView(Static):
    """Widget for discovering and searching podcasts from iTunes API."""

    is_searching = reactive(False)
    search_results = reactive([])

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Discover Podcasts", classes="view-title"),
            Input(placeholder="Search for podcasts", id="search-input"),
            Button(label="Search", id="search-button"),
            Static(id="search-results"),
            id="discover-view"
        )

    def on_mount(self):
        """Set up event handlers when mounted."""
        self.query_one("#search-button").disabled = False

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "search-button":
            self.search_podcasts()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle input submission (when Enter is pressed)."""
        if event.input.id == "search-input":
            self.search_podcasts()

    def search_podcasts(self):
        """Start podcast search with iTunes API."""
        search_term = self.query_one("#search-input").value  # type: ignore

        if not search_term or len(search_term.strip()) == 0:
            self.notify("Please enter a search term", severity="error")
            return

        # Display loading indicator
        self.is_searching = True
        results_widget = self.query_one("#search-results", Static)
        results_widget.update("Searching...")

        # Start search in background
        async def do_search():
            try:
                results = await self.fetch_itunes_podcasts(search_term)
                self.app.call_later(self._update_search_results, results)
            except Exception as e:
                self.app.call_later(self._handle_search_error, str(e))

        asyncio.create_task(do_search())

    async def fetch_itunes_podcasts(self, search_term):
        """Fetch podcast data from iTunes API."""
        # URL encode the search term
        encoded_term = search_term.replace(" ", "+")
        url = f"https://itunes.apple.com/search?term={encoded_term}&entity=podcast&limit=20"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                raise Exception(f"API error: {response.status_code}")

    def _update_search_results(self, results):
        """Update UI with search results."""
        self.is_searching = False
        self.search_results = results

        results_widget = self.query_one("#search-results", Static)

        if not results:
            results_widget.update("No podcasts found.")
            return

        # Format results as rich markdown
        content = []
        for i, podcast in enumerate(results):
            title = podcast.get("collectionName", "Untitled Podcast")
            artist = podcast.get("artistName", "Unknown Artist")
            feed_url = podcast.get("feedUrl", "")

            content.append(f"### {i+1}. {title}")
            content.append(f"By: {artist}")
            if feed_url:
                content.append(f"[Subscribe](@subscribe:{feed_url})")
            content.append("---")

        results_widget.update("\n".join(content))

    def _handle_search_error(self, error_message):
        """Handle search errors."""
        self.is_searching = False
        results_widget = self.query_one("#search-results", Static)
        results_widget.update(f"Error: {error_message}")

    def on_click(self, event):
        """Handle clicks on results - detect subscribe links."""
        if hasattr(event, 'link') and event.link and event.link.startswith("@subscribe:"):
            feed_url = event.link[11:]  # Remove the @subscribe: prefix
            self.add_subscription(feed_url)

    def add_subscription(self, feed_url):
        """Add a subscription to the database."""
        self.notify(f"Adding subscription: {feed_url}")

        # Check if we have access to the feed updater through the app
        if hasattr(self.app, "feed_updater"):
            # Show loading indicator
            self.notify("Adding feed...")

            # Add feed in background
            def do_add_feed():
                try:
                    success, feed = self.app.feed_updater.add_feed(feed_url) # type: ignore
                    self.app.call_from_thread(self._after_add_feed, success, feed_url, feed)
                except Exception as e:
                    self.app.call_from_thread(self._after_add_feed, False, feed_url, str(e))

            import threading
            thread = threading.Thread(target=do_add_feed)
            thread.daemon = True
            thread.start()

    def _after_add_feed(self, success, feed_url, feed_or_error):
        """Handle UI updates after adding a feed."""
        if success:
            self.notify(f"Feed added successfully: {feed_or_error.title}")

            # Refresh feeds list if it exists
            try:
                feeds_list = self.app.query_one("FeedsList")
                feeds_list.load_feeds() # type: ignore
            except Exception:
                pass

            # Switch to library tab
            try:
                tabs = self.app.query_one("#main-tabs")
                tabs.active = "tab-1"  # type: ignore # Assuming "tab-1" is your library tab
            except Exception:
                pass
        else:
            self.notify(f"Failed to add feed: {feed_or_error}", severity="error")
