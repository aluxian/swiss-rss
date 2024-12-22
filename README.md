# Swiss RSS

[![PyPI](https://img.shields.io/pypi/v/swiss-rss)](https://pypi.org/project/swiss-rss/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/swiss-rss)](https://pypi.org/project/swiss-rss/)
[![PyPI - License](https://img.shields.io/pypi/l/swiss-rss)](https://pypi.org/project/swiss-rss/)

RSS web feeds swiss army knife

## Features

- RSS/Atom feed parsing and discovery
- Website favicon download and conversion
- OPML feed list parsing
- Timestamp parsing for multiple formats

## Installation

```sh
pip install swiss-rss
```

## Usage

### Web Feeds

```python
import asyncio
from swiss_rss.web_feeds import parse_feed_from_url, discover_feed

async def main():
    try:
        # Find and parse a feed
        feed_url = await discover_feed("https://2ality.com")
        if not feed_url:
            print("No feed found")
            return

        print(f"Found feed: {feed_url}")
        feed = await parse_feed_from_url(feed_url)

        # Access feed data
        print(f"Title: {feed.title}")
        if feed.items:
            print(f"Latest post: {feed.items[0].title}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
```

### Favicons

```python
from swiss_rss.favicons.favicon_parser import download_favicon

try:
    # Download and convert favicon to 32x32 PNG
    favicon_data = download_favicon("https://example.com")
    if favicon_data:
        with open("favicon.png", "wb") as f:
            f.write(favicon_data)
except Exception as e:
    print(f"Error downloading favicon: {e}")
```

### OPML

```python
from swiss_rss.opml.opml_parser import parse_opml

try:
    with open("feeds.opml") as f:
        feeds = parse_opml(f.read())

    for feed in feeds:
        print(f"Feed: {feed.title} ({feed.xml_url})")
except Exception as e:
    print(f"Error parsing OPML: {e}")
```

### Timestamps

```python
from swiss_rss.timestamps.timestamp_parser import parse_date

# Supports RFC 822, ISO 8601 and other common formats
date = parse_date("Sat, 03 Jun 2023 10:00:00 GMT")
print(f"Parsed date: {date}")
```

### Additional Web Feed Features

```python
from swiss_rss.web_feeds import parse_feed, FeedInfo, FeedItem

# Parse feed content directly
feed_content = '''<?xml version="1.0"?>
<rss version="2.0">
    <!-- RSS content here -->
</rss>'''

feed = parse_feed(feed_content)
# Access additional fields
for item in feed.items:
    print(f"Author: {item.author}")
    print(f"ID: {item.id}")
```

### Additional Favicon Features

```python
from swiss_rss.favicons.favicon_parser import (
    convert_to_png,
    resize_favicon,
    decode_base64_image
)

# Convert image to PNG
png_data = convert_to_png(image_data)

# Resize favicon with custom size
resized_data = resize_favicon(favicon_data, size=64)

# Handle base64 encoded images
image_data = decode_base64_image("data:image/png;base64,...")
```

## Development

1. Clone the repository and install dependencies:

```sh
git clone https://github.com/aluxian/swiss-rss.git
cd swiss-rss
uv venv
source .venv/bin/activate
uv sync
```

2. Run linting checks:

```sh
uv run ruff check .
```

3. Run tests:

```sh
uv run pytest
```

4. Start Aider:

```sh
uvx --python 3.12 --from 'aider-chat[playwright]' --with 'aider-chat[help]' aider
```
