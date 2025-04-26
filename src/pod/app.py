# --------------- Main Application ---------------


from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button, Footer, Header, Static, Label,
     Input, ContentSwitcher, TabPane, Tabs
)
from src.pod.services.databasemanager import PodcastDatabase
from src.pod.services.audioplayer import AudioPlayer
from src.pod.services.downloadmanager import DownloadManager
from src.pod.services.feedupdater import FeedUpdater
from src.pod.widgets.nowplayingbar import NowPlayingBar
from src.pod.widgets.feedslist import FeedsList
from src.pod.widgets.feedview import FeedView
from src.pod.widgets.recentepisodeslist import RecentEpisodesList
from src.pod.widgets.downloadepisodeslist import DownloadedEpisodesList
from src.pod.widgets.addfeeddialog import AddFeedDialog


class PodcastTUIApp(App):
    """Main Podcast TUI application."""

    CSS = """
    #app-grid {
        grid-size: 3;
        grid-rows: 1fr 10;
        grid-columns: 1fr 2fr 1fr;
        height: 100%;
    }

    #header-container {
        row-span: 1;
        column-span: 3;
        height: 3;
        background: $accent;
        color: $text;
    }

    #now-playing {
        row-span: 1;
        column-span: 3;
        height: 5;
        border: solid $accent;
    }

    #main-content {
        row-span: 8;
        column-span: 3;
    }

    .section-title {
        text-style: bold;
        content-align: center middle;
        height: 1;
        margin-bottom: 1;
    }

    .view-title {
        text-style: bold;
        content-align: center middle;
        height: 1;
        margin-bottom: 1;
    }

    #feeds-container {
        height: 100%;
        width: 100%;
        border: solid $accent;
    }

    #episode-title {
        text-style: bold;
    }

    #feed-title {
        color: $text-muted;
    }

    #progress-container {
        height: 1;
        width: 100%;
        margin: 1 0;
    }

    #playback-controls {
        height: 1;
        width: 100%;
        align: center middle;
    }

    .episode-item {
        margin: 1 0;
        padding: 1;
        border: solid $primary-darken-3;
        height: auto;
    }

    .episode-title {
        text-style: bold;
    }

    .feed-name {
        color: $text-muted;
    }

    .episode-duration {
        color: $text-muted;
        text-align: right;
    }

    .episode-description {
        margin-top: 1;
        color: $text-muted;
    }

    .episode-actions {
        margin-top: 1;
        height: 1;
        width: 100%;
    }

    .episode-progress {
        width: 100%;
    }

    #add-feed-dialog {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 60;
        height: 8;
        align: center middle;
    }

    .dialog-title {
        text-style: bold;
        content-align: center middle;
        height: 1;
        margin-bottom: 1;
    }

    #dialog-buttons {
        margin-top: 1;
        height: 1;
        width: 100%;
        align: right middle;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("p", "toggle_play", "Play/Pause"),
        ("left", "seek_backward", "Rewind 10s"),
        ("right", "seek_forward", "Forward 10s"),
        ("+", "speed_up", "Speed Up"),
        ("-", "speed_down", "Speed Down"),
        ("r", "refresh_feeds", "Refresh Feeds"),
        ("s", "search", "Search"),
        ("f", "add_feed", "Add Feed"),
        ("tab", "next_tab", "Next Tab"),
        ("shift+tab", "prev_tab", "Previous Tab"),
    ]

    def __init__(self):
        super().__init__()

        # Initialize core components
        self.database = PodcastDatabase()
        self.player = AudioPlayer()
        self.download_manager = DownloadManager(database=self.database)
        self.feed_updater = FeedUpdater(self.database)

        # Track current view
        self.current_feed_id = None

    def compose(self) -> ComposeResult:
        """Create app layout."""
        yield Header(show_clock=True)

        # Now playing bar
        yield NowPlayingBar(self.player, self.database)

        # Main content with tabs
        with ContentSwitcher(id="main-switcher"):
            with TabPane("Library", id="library-tab"):
                with Horizontal():
                    # Left sidebar - feeds list
                    yield FeedsList(self.database)

                    # Middle - feed view
                    yield FeedView(self.player, self.download_manager)

                    # Right sidebar - recent and downloaded episodes
                    with Vertical():
                        yield RecentEpisodesList(self.database)
                        yield DownloadedEpisodesList(self.database, self.player)

            with TabPane("Discover", id="discover-tab"):
                yield Container(
                    Label("Discover Podcasts", classes="view-title"),
                    Input(placeholder="Search for podcasts", id="search-input"),
                    Static(id="search-results"),
                    id="discover-view"
                )

        # Tab navigation
        yield Tabs("Library", "Discover", id="main-tabs")

        yield Footer()

    def on_mount(self):
        """Set up app when mounted."""
        # # Connect tabs to content switcher
        # tabs = self.query_one("#main-tabs", Tabs)

    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        switcher = self.query_one("#main-switcher", ContentSwitcher)
        switcher.current = event.tab.id


    def action_toggle_play(self):
        """Toggle play/pause."""
        self.player.toggle_playback()

        # Update now playing display
        now_playing = self.query_one(NowPlayingBar)
        now_playing.is_playing = self.player.is_playing

        play_button = now_playing.query_one("#play-pause-button", Button)
        play_button.label = "⏸" if self.player.is_playing else "▶"

    def action_seek_backward(self):
        """Seek backward 10 seconds."""
        self.player.seek(-10)

    def action_seek_forward(self):
        """Seek forward 10 seconds."""
        self.player.seek(10)

    def action_speed_up(self):
        """Increase playback speed."""
        new_speed = min(3.0, self.player.playback_speed + 0.1)
        self.player.set_playback_speed(new_speed)

        # Update display
        now_playing = self.query_one(NowPlayingBar)
        now_playing.playback_speed = new_speed

        speed_display = now_playing.query_one("#speed-display", Label)
        speed_display.update(f"{new_speed:.1f}x")

    def action_speed_down(self):
        """Decrease playback speed."""
        new_speed = max(0.5, self.player.playback_speed - 0.1)
        self.player.set_playback_speed(new_speed)

        # Update display
        now_playing = self.query_one(NowPlayingBar)
        now_playing.playback_speed = new_speed

        speed_display = now_playing.query_one("#speed-display", Label)
        speed_display.update(f"{new_speed:.1f}x")

    def action_refresh_feeds(self):
        """Refresh all feeds."""
        # Show loading indicator
        self.notify("Refreshing feeds...")

        # Update feeds in background
        def do_update():
            results = self.feed_updater.update_all_feeds()
            self.call_from_thread(self._after_feeds_update, results)

        import threading
        thread = threading.Thread(target=do_update)
        thread.daemon = True
        thread.start()

    def _after_feeds_update(self, results):
        """Handle UI updates after feeds are refreshed."""
        # Count successes
        success_count = sum(1 for _, success in results if success)

        # Update UI
        self.notify(f"Updated {success_count}/{len(results)} feeds")

        # Refresh views
        feeds_list = self.query_one(FeedsList)
        feeds_list.load_feeds()

        recent_list = self.query_one(RecentEpisodesList)
        recent_list.load_episodes()

        # Refresh current feed view if active
        if self.current_feed_id:
            self.show_feed(self.current_feed_id)

    def action_add_feed(self):
        """Show add feed dialog."""
        dialog = AddFeedDialog(self.feed_updater)
        self.mount(dialog)

    def action_next_tab(self):
        """Switch to next tab."""
        tabs = self.query_one("#main-tabs", Tabs)
        tabs.action_next_tab()

    def action_prev_tab(self):
        """Switch to previous tab."""
        tabs = self.query_one("#main-tabs", Tabs)
        tabs.action_previous_tab()

    def show_feed(self, feed_id):
        """Show a feed in the feed view."""
        feed = self.database.get_feed(feed_id)
        if feed:
            self.current_feed_id = feed_id
            feed_view = self.query_one(FeedView)
            feed_view.load_feed(feed)
