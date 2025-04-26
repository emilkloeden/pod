# --------------- Database Management ---------------
import json

from datetime import datetime
from typing import List, Optional

from src.pod.config.config import DATABASE_FILE
from src.pod.models.episode import Episode
from src.pod.models.feed import Feed


class PodcastDatabase:
    """Manages podcast feed and episode data."""

    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file
        self.feeds: List[Feed] = []
        self.load()

    def load(self):
        """Load data from file."""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                self.feeds = [Feed.from_dict(feed_data) for feed_data in data["feeds"]]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading database: {e}")
                self.feeds = []
        else:
            self.feeds = []

    def save(self):
        """Save data to file."""
        data = {
            "feeds": [feed.to_dict() for feed in self.feeds]
        }
        with open(self.db_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_feed(self, feed: Feed):
        """Add a new feed."""
        # Check if feed already exists
        for existing_feed in self.feeds:
            if existing_feed.url == feed.url:
                return existing_feed

        self.feeds.append(feed)
        self.save()
        return feed

    def remove_feed(self, feed_id: str):
        """Remove a feed by ID."""
        self.feeds = [feed for feed in self.feeds if feed.id != feed_id]
        self.save()

    def get_feed(self, feed_id: str) -> Optional[Feed]:
        """Get feed by ID."""
        for feed in self.feeds:
            if feed.id == feed_id:
                return feed
        return None

    def get_recent_episodes(self, limit=20) -> List[Episode]:
        """Get most recently published episodes across all feeds."""
        all_episodes = []
        for feed in self.feeds:
            all_episodes.extend(feed.episodes)

        # Sort by publication date, newest first
        all_episodes.sort(key=lambda e: e.pub_date if e.pub_date else datetime.min, reverse=True)
        return all_episodes[:limit]

    def get_downloaded_episodes(self) -> List[Episode]:
        """Get all downloaded episodes."""
        downloaded = []
        for feed in self.feeds:
            downloaded.extend([ep for ep in feed.episodes if ep.downloaded])

        # Sort by download date (we could add a download_date field)
        downloaded.sort(key=lambda e: e.pub_date if e.pub_date else datetime.min, reverse=True)
        return downloaded

    def update_episode_progress(self, feed_id: str, guid: str, position: int):
        """Update playback position for an episode."""
        feed = self.get_feed(feed_id)
        if not feed:
            return

        for episode in feed.episodes:
            if episode.guid == guid:
                episode.play_position = position
                episode.played = True
                self.save()
                break
