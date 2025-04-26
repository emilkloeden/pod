# --------------- Audio Player ---------------
import vlc

from src.pod.models.episode import Episode


class AudioPlayer:
    """Manages audio playback using VLC."""

    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media = None
        self.current_episode = None
        self.is_playing = False
        self.playback_speed = 1.0

    def load(self, episode: Episode):
        """Load an episode for playback."""
        if not episode.downloaded or not episode.download_path:
            return False

        self.current_episode = episode
        self.media = self.instance.media_new(str(episode.download_path))
        self.player.set_media(self.media)

        # Set position if there was previous playback
        if episode.play_position > 0:
            # Convert seconds to milliseconds position
            pos_percent = episode.play_position / episode.duration if episode.duration else 0
            self.player.set_position(pos_percent)

        return True

    def play(self):
        """Start or resume playback."""
        if not self.media:
            return False

        self.player.play()
        self.is_playing = True
        return True

    def pause(self):
        """Pause playback."""
        if not self.is_playing:
            return

        self.player.pause()
        self.is_playing = False

    def toggle_playback(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def stop(self):
        """Stop playback and save position."""
        if not self.current_episode:
            return

        if self.is_playing:
            self.pause()

        # Save current position
        position_ms = self.player.get_time()
        if position_ms >= 0:
            self.current_episode.play_position = position_ms // 1000  # Convert ms to seconds

        self.player.stop()
        self.is_playing = False

    def seek(self, offset: int):
        """Seek forward/backward by offset seconds."""
        if not self.media:
            return

        current_pos = self.player.get_time() // 1000  # In seconds
        new_pos = max(0, current_pos + offset)

        # Convert to VLC position (0.0 to 1.0)
        if self.current_episode and self.current_episode.duration:
            pos_percent = new_pos / self.current_episode.duration
            self.player.set_position(min(pos_percent, 1.0))

    def set_playback_speed(self, speed: float):
        """Set playback speed (0.5 to 3.0)."""
        if not self.media:
            return

        speed = max(0.5, min(3.0, speed))
        self.player.set_rate(speed)
        self.playback_speed = speed

    def get_current_position(self) -> int:
        """Get current playback position in seconds."""
        if not self.media or not self.is_playing:
            return 0

        position_ms = self.player.get_time()
        return position_ms // 1000 if position_ms >= 0 else 0

    def get_duration(self) -> int:
        """Get media duration in seconds."""
        if not self.media:
            return 0

        duration_ms = self.player.get_length()
        return duration_ms // 1000 if duration_ms >= 0 else 0
