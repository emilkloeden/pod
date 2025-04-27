from textual.app import  ComposeResult
from textual.containers import Container, Horizontal
from textual.css.query import NoMatches
from textual.widgets import (
    Button, Static, Label, ProgressBar
)

from src.pod.models.feed import Feed
from src.pod.services.audioplayer import AudioPlayer
from src.pod.services.downloadmanager import DownloadManager
from src.pod.widgets.nowplayingbar import NowPlayingBar


class FeedView(Static):
    """View showing details of a single feed."""

    def __init__(self, player: AudioPlayer, download_manager: DownloadManager):
        super().__init__()
        self.player = player
        self.download_manager = download_manager
        self.current_feed = None

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Label("Feed Title", id="feed-title", classes="view-title"),
                Label("Feed Author", id="feed-author"),
                id="feed-header"
            ),
            Container(
                Label("Episodes", classes="section-title"),
                Static(id="feed-episodes-list"),
                id="feed-episodes"
            ),
            id="feed-view"
        )

    def load_feed(self, feed: Feed):
        """Load a feed into the view."""
        self.current_feed = feed

        # Update header
        title = self.query_one("#feed-title", Label)
        author = self.query_one("#feed-author", Label)
        title.update(feed.title)
        author.update(feed.author)

        # Load episodes
        episodes_list = self.query_one("#feed-episodes-list", Static)
        episodes_list.remove_children()

        for episode in feed.episodes:
            # Create episode container
            episode_container = Container(
                Label(episode.title, classes="episode-title"),
                Label(f"Published: {episode.pub_date.strftime('%Y-%m-%d') if episode.pub_date else 'Unknown'}", classes="episode-date"),
                Label(f"Duration: {episode.format_duration()}", classes="episode-duration"),
                Static(episode.description[:150] + "..." if len(episode.description) > 150 else episode.description, classes="episode-description"),
                Horizontal(
                    Button("▶" if episode.downloaded else "⬇", id=f"play-dl-{episode.guid}",
                           variant="success" if episode.downloaded else "default",
                           disabled=not episode.downloaded and not episode.audio_url),
                    ProgressBar(id=f"progress-{episode.guid}", classes="episode-progress", show_bar=episode.downloaded),
                    classes="episode-actions"
                ),
                classes="episode-item",
                id=f"episode-{episode.guid}"
            )

            episodes_list.mount(episode_container)

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id

        if button_id and button_id.startswith("play-dl-"):
            guid = button_id.replace("play-dl-", "")
            episode = self._find_episode(guid)

            if episode:
                if episode.downloaded:
                    # Play the episode
                    self.player.stop()
                    if self.player.load(episode):
                        self.player.play()
                        # Update now playing bar
                        now_playing = self.app.query_one(NowPlayingBar)
                        if self.current_feed:
                            now_playing.update_episode(episode, self.current_feed)
                else:
                    # Download the episode
                    self._download_episode(episode)

    def _find_episode(self, guid):
        """Find an episode by GUID in the current feed."""
        if not self.current_feed:
            return None

        for episode in self.current_feed.episodes:
            if episode.guid == guid:
                return episode

        return None

    def _download_episode(self, episode):
        """Start downloading an episode."""
        # Start download in a worker thread
        def do_download():
            success = self.download_manager.download_episode(episode, self.current_feed)
            # Update UI after download
            self.app.call_from_thread(self._update_after_download, episode, success)

        # Show progress indicator
        button = self.query_one(f"#play-dl-{episode.guid}", Button)
        button.label = "⏳"
        button.disabled = True

        # Start download thread
        import threading
        thread = threading.Thread(target=do_download)
        thread.daemon = True
        thread.start()

        # Start progress update timer
        self._start_progress_update(episode.guid)

    def _start_progress_update(self, guid):
        """Start timer to update download progress."""
        def update_progress():
            progress = self.download_manager.get_download_progress(guid)
            try:
                progress_bar = self.query_one(f"#progress-{guid}", ProgressBar)
                progress_bar.visible = True
                progress_bar.progress = progress

                # Continue timer if download in progress
                if progress < 100 and progress > 0:
                    self.set_timer(0.5, update_progress)
            except NoMatches:
                pass

        # Start first update
        self.set_timer(0.5, update_progress)

    def _update_after_download(self, episode, success):
        """Update UI after download completes."""
        button = self.query_one(f"#play-dl-{episode.guid}", Button)

        if success:
            button.label = "▶"
            button.variant = "success"
            button.disabled = False
        else:
            button.label = "⬇"
            button.variant = "error"
            button.disabled = False
