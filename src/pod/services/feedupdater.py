# --------------- Feed Updater ---------------
from datetime import datetime
from typing import Optional

from src.pod.models.episode import Episode
from src.pod.models.feed import Feed
from src.pod.services.databasemanager import PodcastDatabase
from src.pod.services.rss import PodcastRSSParser

class FeedUpdater:
    """Updates podcast feeds from RSS."""

    def __init__(self, database: PodcastDatabase):
        self.database = database
        self.parser = PodcastRSSParser()

    def add_feed_from_url(self, url: str) -> Optional[Feed]:
        """Add a new feed from URL."""
        try:
            # Parse feed
            feed_data = self.parser.parse_feed(url)
            if not feed_data:
                return None

            # Create feed
            feed = Feed(
                title=feed_data["title"],
                url=url,
                author=feed_data.get("author", "Unknown"),
                description=feed_data.get("description", ""),
                image_url=feed_data.get("image_url")
            )

            # Add episodes
            for ep_data in feed_data.get("episodes", []):
                pub_date = ep_data.get("pub_date")
                duration_seconds = ep_data.get("duration_seconds", 0)

                episode = Episode(
                    title=ep_data.get("title", "Untitled"),
                    audio_url=ep_data.get("audio_url", ""),
                    pub_date=pub_date,
                    description=ep_data.get("description", ""),
                    duration=duration_seconds,
                    feed_id=feed.id,
                    guid=ep_data.get("guid", ""),
                    image_url=ep_data.get("image_url")
                )
                feed.episodes.append(episode)

            # Add to database
            return self.database.add_feed(feed)

        except Exception as e:
            print(f"Error adding feed: {e}")
            return None

    def update_feed(self, feed: Feed) -> bool:
        """Update an existing feed."""
        try:
            # Parse feed
            feed_data = self.parser.parse_feed(feed.url)
            if not feed_data:
                return False

            # Update feed metadata
            feed.title = feed_data["title"]
            feed.author = feed_data.get("author", "Unknown")
            feed.description = feed_data.get("description", "")
            feed.image_url = feed_data.get("image_url")
            feed.last_updated = datetime.now()

            # Track existing episodes by GUID
            existing_episodes = {ep.guid: ep for ep in feed.episodes}

            # Update episodes
            new_episodes = []
            for ep_data in feed_data.get("episodes", []):
                guid = ep_data.get("guid", "")

                if guid in existing_episodes:
                    # Episode exists, keep existing data
                    continue
                else:
                    # New episode
                    pub_date = ep_data.get("pub_date")
                    duration_seconds = ep_data.get("duration_seconds", 0)

                    episode = Episode(
                        title=ep_data.get("title", "Untitled"),
                        audio_url=ep_data.get("audio_url", ""),
                        pub_date=pub_date,
                        description=ep_data.get("description", ""),
                        duration=duration_seconds,
                        feed_id=feed.id,
                        guid=guid,
                        image_url=ep_data.get("image_url")
                    )
                    new_episodes.append(episode)

            # Add new episodes
            feed.episodes.extend(new_episodes)

            # Sort episodes by date (newest first)
            feed.episodes.sort(key=lambda e: e.pub_date if e.pub_date else datetime.min, reverse=True)

            # Save database
            self.database.save()

            return True

        except Exception as e:
            print(f"Error updating feed: {e}")
            return False

    def update_all_feeds(self):
        """Update all feeds in the database."""
        results = []
        for feed in self.database.feeds:
            success = self.update_feed(feed)
            results.append((feed.title, success))
        return results
