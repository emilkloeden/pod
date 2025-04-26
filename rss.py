import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import email.utils
import re


class PodcastRSSParser:
    def __init__(self):
        # Define XML namespaces used in podcast feeds
        self.namespaces = {
            "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
            "content": "http://purl.org/rss/1.0/modules/content/",
            "podcast": "https://podcastindex.org/namespace/1.0",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        # Register namespaces with ElementTree for easier parsing
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)

    def parse_feed(self, feed_url):
        """
        Parse a podcast RSS feed and return structured data
        """
        try:
            # Fetch the RSS feed content
            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors

            # Parse XML content
            root = ET.fromstring(response.content)

            # Extract channel (podcast) information
            channel = root.find("channel")

            # Parse podcast metadata
            podcast_info = {
                "title": self._get_text(channel, "title"),
                "description": self._get_text(channel, "description"),
                "link": self._get_text(channel, "link"),
                "language": self._get_text(channel, "language"),
                "copyright": self._get_text(channel, "copyright"),
                "last_build_date": self._parse_date(
                    self._get_text(channel, "lastBuildDate")
                ),
                "image_url": self._get_channel_image(channel),
                "author": self._get_text(channel, "./itunes:author", self.namespaces),
                "owner": self._get_owner_info(channel),
                "categories": self._get_categories(channel),
                "explicit": self._get_text(
                    channel, "./itunes:explicit", self.namespaces
                )
                == "yes",
                "episodes": [],
            }

            # Extract episodes
            items = channel.findall("item")
            for item in items:
                episode = self._parse_episode(item)
                podcast_info["episodes"].append(episode)

            return podcast_info

        except requests.RequestException as e:
            print(f"Error fetching feed: {e}")
            return None
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def _get_text(self, element, xpath, namespaces=None):
        """Extract text from an element with proper error handling"""
        try:
            found = element.find(xpath, namespaces)
            return found.text.strip() if found is not None and found.text else None
        except (AttributeError, TypeError):
            return None

    def _get_channel_image(self, channel):
        """Get the best available image for the podcast"""
        # Try iTunes image first (usually higher quality)
        itunes_image = channel.find("./itunes:image", self.namespaces)
        if itunes_image is not None and "href" in itunes_image.attrib:
            return itunes_image.attrib["href"]

        # Fall back to standard RSS image
        image_elem = channel.find("./image/url")
        if image_elem is not None and image_elem.text:
            return image_elem.text.strip()

        return None

    def _get_owner_info(self, channel):
        """Extract owner information from the feed"""
        owner_elem = channel.find("./itunes:owner", self.namespaces)
        if owner_elem is not None:
            return {
                "name": self._get_text(owner_elem, "./itunes:name", self.namespaces),
                "email": self._get_text(owner_elem, "./itunes:email", self.namespaces),
            }
        return None

    def _get_categories(self, channel):
        """Extract iTunes categories with hierarchical structure"""
        categories = []
        category_elements = channel.findall("./itunes:category", self.namespaces)

        for category_elem in category_elements:
            category = {}
            if "text" in category_elem.attrib:
                category["name"] = category_elem.attrib["text"]

                # Check for subcategories
                subcategories = []
                for subcategory in category_elem.findall(
                    "./itunes:category", self.namespaces
                ):
                    if "text" in subcategory.attrib:
                        subcategories.append(subcategory.attrib["text"])

                if subcategories:
                    category["subcategories"] = subcategories

                categories.append(category)

        return categories

    def _parse_episode(self, item):
        """Parse a single episode item"""
        # Extract enclosure (audio file) information
        enclosure = item.find("./enclosure")
        audio_url = (
            enclosure.attrib["url"]
            if enclosure is not None and "url" in enclosure.attrib
            else None
        )
        audio_length = (
            enclosure.attrib["length"]
            if enclosure is not None and "length" in enclosure.attrib
            else None
        )
        audio_type = (
            enclosure.attrib["type"]
            if enclosure is not None and "type" in enclosure.attrib
            else None
        )

        # Extract episode image
        episode_image = item.find("./itunes:image", self.namespaces)
        image_url = (
            episode_image.attrib["href"]
            if episode_image is not None and "href" in episode_image.attrib
            else None
        )

        # Parse duration into seconds
        duration_str = self._get_text(item, "./itunes:duration", self.namespaces)
        duration_seconds = self._parse_duration(duration_str)

        # Extract chapters
        chapters_elem = item.find("./podcast:chapters", self.namespaces)
        chapters = None
        if chapters_elem is not None:
            chapters = {
                "url": chapters_elem.attrib.get("url"),
                "type": chapters_elem.attrib.get("type"),
            }

        # Extract transcript
        transcript_elem = item.find("./podcast:transcript", self.namespaces)
        transcript = None
        if transcript_elem is not None:
            transcript = {
                "url": transcript_elem.attrib.get("url"),
                "type": transcript_elem.attrib.get("type"),
                "language": transcript_elem.attrib.get("language", "en"),
            }

        # Build episode object
        episode = {
            "title": self._get_text(item, "./title"),
            "description": self._get_text(item, "./description"),
            "content_encoded": self._get_text(
                item, "./content:encoded", self.namespaces
            ),
            "pub_date": self._parse_date(self._get_text(item, "./pubDate")),
            "guid": self._get_text(item, "./guid"),
            "link": self._get_text(item, "./link"),
            "audio_url": audio_url,
            "audio_size": int(audio_length)
            if audio_length and audio_length.isdigit()
            else None,
            "audio_type": audio_type,
            "image_url": image_url,
            "duration": duration_str,
            "duration_seconds": duration_seconds,
            "explicit": self._get_text(item, "./itunes:explicit", self.namespaces)
            == "yes",
            "episode_number": self._get_text(item, "./itunes:episode", self.namespaces),
            "season_number": self._get_text(item, "./itunes:season", self.namespaces),
            "episode_type": self._get_text(
                item, "./itunes:episodeType", self.namespaces
            ),
            "chapters": chapters,
            "transcript": transcript,
        }

        return episode

    def _parse_date(self, date_str):
        """Parse RFC 2822 date string to datetime object"""
        if not date_str:
            return None

        try:
            time_tuple = email.utils.parsedate_tz(date_str)
            if time_tuple:
                return datetime(*time_tuple[:6])
        except Exception:
            pass

        # Try various formats if standard parsing fails
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_duration(self, duration_str):
        """Convert duration string to seconds"""
        if not duration_str:
            return None

        # Try to convert direct seconds
        if duration_str.isdigit():
            return int(duration_str)

        # Handle HH:MM:SS format
        if ":" in duration_str:
            parts = duration_str.split(":")

            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = parts
                return int(minutes) * 60 + int(seconds)

        return None


# Example usage
if __name__ == "__main__":
    parser = PodcastRSSParser()

    # Example feed URLs
    feed_urls = [
        #    "https://feeds.megaphone.fm/stuffyoushouldknow",
        "https://feeds.npr.org/510289/podcast.xml",
        "https://feeds.simplecast.com/54nAGcIl",
    ]

    # Parse and display basic info for a feed
    feed_url = feed_urls[0]  # Change index to try different feeds

    print(f"Parsing feed: {feed_url}")
    podcast_data = parser.parse_feed(feed_url)

    if podcast_data:
        print(f"\nPodcast: {podcast_data['title']}")
        print(f"Author: {podcast_data['author']}")
        print(f"Episodes: {len(podcast_data['episodes'])}")

        # Display the most recent episode
        if podcast_data["episodes"]:
            latest = podcast_data["episodes"][0]
            print("\nLatest episode:")
            print(f"Title: {latest['title']}")
            print(f"Published: {latest['pub_date']}")
            print(
                f"Duration: {latest['duration']} ({latest['duration_seconds']} seconds)"
            )
            print(f"Audio: {latest['audio_url']}")
    else:
        print("Failed to parse feed")
