import argparse
import requests
from dataclasses import dataclass
from src.pod.services.rss import PodcastRSSParser


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--term", type=str, required=True)
    return parser.parse_args()


def parse_results(j):
    # result_count = j["resultCount"]
    results = j["results"]
    return [parse_result(result) for result in results]


@dataclass
class ITunesResult:
    artist: str
    artist_id: int
    collection: str
    collection_id: int
    feed_url: str


def parse_result(result):
    return ITunesResult(
        artist=result["artistName"],
        artist_id=result["artistId"],
        collection=result["collectionName"],
        collection_id=result["collectionId"],
        feed_url=result["feedUrl"],
    )


def fetch_feed(url):
    r = requests.get(url)
    if r.status_code != 200:
        print(f"{url} - {r.status_code}")
        return None
    print(r.text)


def main():
    args = parse_args()
    params = {
        "limit": args.limit,
        "media": "podcast",
        "term": args.term,
        "language": "EN",
        "attribute": "titleTerm",
        "entity": "podcast",
    }
    # print(params)
    url = "https://itunes.apple.com/search?"
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(r.status_code)
        exit()
    d = r.json()

    query_results = parse_results(d)
    p = PodcastRSSParser()
    for result in query_results:
        print(result.feed_url)
        podcast_data = p.parse_feed(result.feed_url)
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
        # fetch_feed(result.feed_url)


if __name__ == "__main__":
    main()
