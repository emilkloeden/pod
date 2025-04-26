from datetime import datetime
from typing import Any, Dict, List, Optional

from src.pod.models.episode import Episode

class Feed:
    """Represents a podcast feed/subscription."""

    def __init__(self,
                title: str,
                url: str,
                author: str,
                description: str,
                image_url: Optional[str] = None):
        self.title = title
        self.url = url
        self.author = author
        self.description = description
        self.image_url = image_url
        self.episodes: List[Episode] = []
        self.last_updated = datetime.now()
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate a unique ID for the feed."""
        # Simple URL-based ID
        import hashlib
        return hashlib.md5(self.url.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "description": self.description,
            "image_url": self.image_url,
            "last_updated": self.last_updated.isoformat(),
            "episodes": [episode.to_dict() for episode in self.episodes]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feed':
        """Create Feed from dictionary."""
        feed = cls(
            title=data["title"],
            url=data["url"],
            author=data["author"],
            description=data["description"],
            image_url=data["image_url"]
        )
        feed.id = data["id"]
        feed.last_updated = datetime.fromisoformat(data["last_updated"])
        feed.episodes = [Episode.from_dict(ep_data) for ep_data in data["episodes"]]
        return feed
