# --------------- Download Manager ---------------
from pathlib import Path

import requests

from src.pod.config.config import DOWNLOADS_DIR
from src.pod.models.episode import Episode
from src.pod.models.feed import Feed


class DownloadManager:
    """Manages episode downloading."""

    def __init__(self, download_dir=DOWNLOADS_DIR, database=None):
        self.download_dir = download_dir
        self.database = database
        self.current_downloads = {}  # track in-progress downloads

    def download_episode(self, episode: Episode, feed: Feed):
        """Download an episode."""
        # Create feed directory
        feed_dir = self.download_dir / feed.id
        feed_dir.mkdir(exist_ok=True)

        # Determine file path
        filename = f"{episode.guid}.mp3"  # Using guid ensures uniqueness
        filepath = feed_dir / filename

        try:
            # Stream download with progress tracking
            r = requests.get(episode.audio_url, stream=True)
            r.raise_for_status()

            content_length = int(r.headers.get('content-length', 0))

            with open(filepath, 'wb') as f:
                if content_length == 0:
                    # No content length header
                    f.write(r.content)
                else:
                    # Stream with progress
                    dl = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            dl += len(chunk)
                            f.write(chunk)
                            # Update progress
                            progress = (dl / content_length) * 100
                            self.current_downloads[episode.guid] = progress

            # Update episode
            episode.downloaded = True
            episode.download_path = filepath

            # Save database
            if self.database:
                self.database.save()

            # Remove from current downloads
            if episode.guid in self.current_downloads:
                del self.current_downloads[episode.guid]

            return True

        except Exception as e:
            print(f"Download error: {e}")
            # Clean up failed download
            if filepath.exists():
                filepath.unlink()
            return False

    def get_download_progress(self, episode_guid: str) -> float:
        """Get download progress percentage for an episode."""
        return self.current_downloads.get(episode_guid, 0.0)

    def delete_downloaded_episode(self, episode: Episode):
        """Delete a downloaded episode."""
        if episode.downloaded and episode.download_path:
            try:
                # Delete file
                if Path(episode.download_path).exists():
                    Path(episode.download_path).unlink()

                # Update episode
                episode.downloaded = False
                episode.download_path = None

                # Save database
                if self.database:
                    self.database.save()

                return True
            except Exception as e:
                print(f"Delete error: {e}")
                return False
        return False
