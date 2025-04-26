from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button, Static, Label, ProgressBar
)

from src.pod.services.databasemanager import PodcastDatabase
from src.pod.services.audioplayer import AudioPlayer
from src.pod.widgets.nowplayingbar import NowPlayingBar


class DownloadedEpisodesList(Static):
    """Widget showing downloaded episodes."""

    def __init__(self, database: PodcastDatabase, player: AudioPlayer):
        super().__init__()
        self.database = database
        self.player = player

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Downloaded Episodes", classes="section-title"),
            Static(id="downloaded-list"),
            id="downloaded-episodes"
        )

    def on_mount(self):
        """Load episodes when mounted."""
        self.load_episodes()

    def load_episodes(self):
        """Load downloaded episodes."""
        episodes_container = self.query_one("#downloaded-list", Static)
        episodes_container.remove_children()

        downloaded = self.database.get_downloaded_episodes()

        for episode in downloaded:
            feed = self.database.get_feed(episode.feed_id)
            feed_name = feed.title if feed else "Unknown"

            progress = episode.play_progress_percent()

            episode_container = Container(
                Label(f"{episode.title}", classes="episode-title"),
                Label(f"({feed_name})", classes="feed-name"),
                Horizontal(
                    ProgressBar(progress, classes="episode-progress"),
                    Label(episode.format_play_progress(), classes="episode-progress-text"),
                    classes="episode-progress-container"
                ),
                Horizontal(
                    Button("▶", id=f"play-{episode.guid}", classes="play-button"),
                    Button("🗑", id=f"delete-{episode.guid}", classes="delete-button"),
                    classes="episode-buttons"
                ),
                classes="downloaded-item",
                id=f"downloaded-{episode.guid}"
            )

            episodes_container.mount(episode_container)

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id

        if button_id and button_id.startswith("play-"):
            guid = button_id.replace("play-", "")
            self.play_episode(guid)

        elif button_id and button_id.startswith("delete-"):
            guid = button_id.replace("delete-", "")
            self.delete_episode(guid)

    def play_episode(self, guid: str):
        """Play an episode by GUID."""
        for feed in self.database.feeds:
            for episode in feed.episodes:
                if episode.guid == guid and episode.downloaded:
                    self.player.stop()  # Stop current playback
                    if self.player.load(episode):
                        self.player.play()
                        # Update now playing bar
                        try:
                            now_playing = self.app.query_one(NowPlayingBar)
                            now_playing.update_episode(episode, feed)
                        except:
                            # Claude got cut off and thus this does too
                            raise

    def delete_episode(self, guid: str):
        """Delete a downloaded episode by GUID."""
        for feed in self.database.feeds:
            for episode in feed.episodes:
                if episode.guid == guid and episode.downloaded:
                    # Get reference to download manager
                    download_manager = self.app.download_manager
                    if download_manager.delete_downloaded_episode(episode):
                        # Refresh list
                        self.load_episodes()
                    break
