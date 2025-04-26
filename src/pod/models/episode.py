from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class Episode:
    """Represents a podcast episode."""

    def __init__(self,
                title: str,
                audio_url: str,
                pub_date: Optional[datetime],
                description: str,
                duration: int,
                feed_id: str,
                guid: str,
                image_url: Optional[str] = None):
        self.title = title
        self.audio_url = audio_url
        self.pub_date = pub_date
        self.description = description
        self.duration = duration  # in seconds
        self.feed_id = feed_id
        self.guid = guid
        self.image_url = image_url
        self.downloaded = False
        self.download_path = None
        self.played = False
        self.play_position = 0  # in seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "title": self.title,
            "audio_url": self.audio_url,
            "pub_date": self.pub_date.isoformat() if self.pub_date else None,
            "description": self.description,
            "duration": self.duration,
            "feed_id": self.feed_id,
            "guid": self.guid,
            "image_url": self.image_url,
            "downloaded": self.downloaded,
            "download_path": str(self.download_path) if self.download_path else None,
            "played": self.played,
            "play_position": self.play_position
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Episode':
        """Create Episode from dictionary."""
        episode = cls(
            title=data["title"],
            audio_url=data["audio_url"],
            pub_date=datetime.fromisoformat(data["pub_date"]) if data["pub_date"] else None,
            description=data["description"],
            duration=data["duration"],
            feed_id=data["feed_id"],
            guid=data["guid"],
            image_url=data["image_url"]
        )
        episode.downloaded = data["downloaded"]
        episode.download_path = Path(data["download_path"]) if data["download_path"] else None
        episode.played = data["played"]
        episode.play_position = data["play_position"]
        return episode

    def format_duration(self) -> str:
        """Format duration as MM:SS or HH:MM:SS."""
        if not self.duration:
            return "00:00"

        minutes, seconds = divmod(self.duration, 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def format_play_progress(self) -> str:
        """Format play progress as MM:SS / MM:SS."""
        played = self.format_time(self.play_position)
        total = self.format_duration()
        return f"{played}/{total}"

    def format_time(self, seconds: int) -> str:
        """Format time in seconds as MM:SS or HH:MM:SS."""
        if not seconds:
            return "00:00"

        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def play_progress_percent(self) -> float:
        """Calculate play progress as percentage."""
        if not self.duration or self.duration == 0:
            return 0
        return (self.play_position / self.duration) * 100
