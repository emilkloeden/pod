from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.css.query import NoMatches
from textual.widgets import (
    Button, Static, Label, ProgressBar
)
from textual.reactive import reactive

from src.pod.models.episode import Episode
from src.pod.models.feed import Feed
from src.pod.services.audioplayer import AudioPlayer
from src.pod.services.databasemanager import PodcastDatabase


class NowPlayingBar(Static):
    """Widget showing currently playing episode with controls."""

    current_position = reactive(0)
    current_duration = reactive(0)
    is_playing = reactive(False)
    current_title = reactive("No Episode Playing")
    current_feed = reactive("")
    playback_speed = reactive(1.0)

    def __init__(self, player: AudioPlayer, database: PodcastDatabase):
        super().__init__()
        self.player = player
        self.database = database
        self.update_timer = None

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.current_title, id="episode-title"),
            Label(self.current_feed, id="feed-title"),
            Horizontal(
                ProgressBar(id="playback-progress", show_percentage=False),
                Label("00:00/00:00", id="time-display"),
                id="progress-container"
            ),
            Horizontal(
                Button("⏮", id="prev-button", variant="primary"),
                Button("⏯", id="play-pause-button", variant="success"),
                Button("⏭", id="next-button", variant="primary"),
                Button("-10s", id="rewind-button"),
                Label(f"{self.playback_speed}x", id="speed-display"),
                Button("+10s", id="forward-button"),
                id="playback-controls"
            ),
            id="now-playing"
        )

    def on_mount(self):
        """Start the update timer when mounted."""
        self.update_timer = self.set_interval(0.5, self.update_progress)

    def update_progress(self):
        """Update playback progress."""
        if not self.player.current_episode:
            return

        # Update position
        self.current_position = self.player.get_current_position()
        self.current_duration = self.player.current_episode.duration
        self.is_playing = self.player.is_playing

        # Update display
        try:
            progress_bar = self.query_one("#playback-progress", ProgressBar)
            time_display = self.query_one("#time-display", Label)

            if self.current_duration > 0:
                progress = (self.current_position / self.current_duration) * 100
                progress_bar.progress = progress
            else:
                progress_bar.progress = 0

            # Format time
            position_str = self.format_time(self.current_position)
            duration_str = self.format_time(self.current_duration)
            time_display.update(f"{position_str}/{duration_str}")

            # Save progress periodically
            if self.player.current_episode and self.is_playing:
                episode = self.player.current_episode
                self.database.update_episode_progress(
                    episode.feed_id,
                    episode.guid,
                    self.current_position
                )

        except NoMatches:
            pass

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "play-pause-button":
            self.player.toggle_playback()
            self.is_playing = self.player.is_playing
            event.button.label = "⏸" if self.is_playing else "▶"

        elif button_id == "rewind-button":
            self.player.seek(-10)  # Back 10 seconds

        elif button_id == "forward-button":
            self.player.seek(10)  # Forward 10 seconds

    def update_episode(self, episode: Episode, feed: Feed):
        """Update displayed episode."""
        self.current_title = episode.title
        self.current_feed = feed.title

        # Format display
        episode_title = self.query_one("#episode-title", Label)
        feed_title = self.query_one("#feed-title", Label)
        episode_title.update(self.current_title)
        feed_title.update(self.current_feed)

        # Reset play button
        play_button = self.query_one("#play-pause-button", Button)
        play_button.label = "⏸" if self.is_playing else "▶"

    def format_time(self, seconds: int) -> str:
        """Format time in seconds as MM:SS or HH:MM:SS."""
        if not seconds:
            return "00:00"

        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
