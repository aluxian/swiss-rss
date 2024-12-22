from .web_feeds import FeedInfo, parse_feed, discover_feed, parse_feed_from_url
import pytest
from aioresponses import aioresponses
import aiohttp


rss_data = """
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example RSS Feed</title>
    <link>https://example.com</link>
    <description>This is an example RSS feed.</description>
    <item>
      <title>RSS Item 1</title>
      <link>https://example.com/item1</link>
      <description>This is the first RSS item.</description>
      <pubDate>Sat, 03 Jun 2023 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>RSS Item 2</title>
      <link>https://example.com/item2</link>
      <description>This is the second RSS item.</description>
      <pubDate>Sun, 04 Jun 2023 12:30:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

atom_data = """
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Example Atom Feed</title>
  <link href="https://example.com"/>
  <subtitle>This is an example Atom feed.</subtitle>
  <entry>
    <title>Atom Entry 1</title>
    <link href="https://example.com/entry1"/>
    <summary>This is the first Atom entry.</summary>
    <published>2023-06-03T10:00:00Z</published>
  </entry>
  <entry>
    <title>Atom Entry 2</title>
    <link href="https://example.com/entry2"/>
    <summary>This is the second Atom entry.</summary>
    <updated>2023-06-04T12:30:00Z</updated>
  </entry>
</feed>
"""


def test_parse_rss():
    feed_info = parse_feed(rss_data)
    assert isinstance(feed_info, FeedInfo)
    assert feed_info.title == "Example RSS Feed"
    assert feed_info.link == "https://example.com"
    assert feed_info.description == "This is an example RSS feed."
    assert len(feed_info.items) == 2
    assert feed_info.items[0].title == "RSS Item 1"
    assert feed_info.items[0].link == "https://example.com/item1"
    assert feed_info.items[0].description == "This is the first RSS item."
    assert str(feed_info.items[0].pub_date) == "2023-06-03 10:00:00+00:00"
    assert str(feed_info.items[1].pub_date) == "2023-06-04 12:30:00+00:00"
    assert feed_info.items[1].title == "RSS Item 2"
    assert feed_info.items[1].link == "https://example.com/item2"
    assert feed_info.items[1].description == "This is the second RSS item."


def test_parse_rss_with_smart_quotes():
    rss_with_quotes = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <description>Test feed with smart quotes</description>
    <item>
      <title>The new ‘pay or consent’ scheme in media</title>
      <link>https://example.com/article</link>
      <description>Article with "smart" quotes</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

    feed_info = parse_feed(rss_with_quotes)
    assert feed_info.items[0].title == "The new ‘pay or consent’ scheme in media"


@pytest.mark.asyncio
async def test_discover_feed_from_html():
    html_content = """
    <html>
        <head>
            <link rel="alternate" type="application/rss+xml" href="/feed.xml">
            <link rel="alternate" type="application/atom+xml" href="/atom.xml">
        </head>
        <body>
            <a href="/rss">RSS Feed</a>
        </body>
    </html>
    """

    feed_content = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>http://example.com</link>
            <description>Test feed</description>
            <item>
                <title>Test Item</title>
                <link>http://example.com/item1</link>
            </item>
        </channel>
    </rss>
    """

    with aioresponses() as m:
        # Mock the HTML page
        m.get("http://example.com", status=200, body=html_content)
        # Mock the potential feed URLs
        m.get("http://example.com/feed.xml", status=200, body=feed_content)
        m.get("http://example.com/atom.xml", status=404)
        m.get("http://example.com/rss", status=404)

        async with aiohttp.ClientSession() as session:
            feed_url = await discover_feed("http://example.com", session)
            assert feed_url == "http://example.com/feed.xml"


@pytest.mark.asyncio
async def test_discover_feed_no_feeds():
    html_content = """
    <html>
        <head>
            <title>No feeds here</title>
        </head>
        <body>
            <p>Just a regular page</p>
        </body>
    </html>
    """

    with aioresponses() as m:
        m.get("http://example.com", status=200, body=html_content)

        async with aiohttp.ClientSession() as session:
            feed_url = await discover_feed("http://example.com", session)
            assert feed_url is None


@pytest.mark.asyncio
async def test_discover_feed_invalid_feeds():
    html_content = """
    <html>
        <head>
            <link rel="alternate" type="application/rss+xml" href="/feed.xml">
        </head>
    </html>
    """

    invalid_feed = """
    <html>
        <body>
            Not a valid feed
        </body>
    </html>
    """

    with aioresponses() as m:
        m.get("http://example.com", status=200, body=html_content)
        m.get("http://example.com/feed.xml", status=200, body=invalid_feed)

        async with aiohttp.ClientSession() as session:
            feed_url = await discover_feed("http://example.com", session)
            assert feed_url is None


def test_parse_atom():
    feed_info = parse_feed(atom_data)
    assert isinstance(feed_info, FeedInfo)
    assert feed_info.title == "Example Atom Feed"
    assert feed_info.link == "https://example.com"
    assert feed_info.description == "This is an example Atom feed."
    assert len(feed_info.items) == 2
    assert feed_info.items[0].title == "Atom Entry 1"
    assert feed_info.items[0].link == "https://example.com/entry1"
    assert feed_info.items[0].description == "This is the first Atom entry."
    assert str(feed_info.items[0].pub_date) == "2023-06-03 10:00:00+00:00"
    assert feed_info.items[1].title == "Atom Entry 2"
    assert feed_info.items[1].link == "https://example.com/entry2"
    assert feed_info.items[1].description == "This is the second Atom entry."


def test_parse_rss_with_guid():
    rss_content = """
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>http://example.com</link>
            <description>A test feed</description>
            <item>
                <title>Test Item</title>
                <link>http://example.com/item</link>
                <guid>unique-id-1</guid>
                <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """
    feed_info = parse_feed(rss_content)
    assert len(feed_info.items) == 1
    assert feed_info.items[0].id == "unique-id-1"


def test_parse_rss_without_guid_or_link():
    rss_content = """
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>http://example.com</link>
            <description>A test feed</description>
            <item>
                <title>Test Item</title>
                <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """
    feed_info = parse_feed(rss_content)
    assert len(feed_info.items) == 1
    assert (
        feed_info.items[0].id == ""
    )  # Empty string when both guid and link are missing


def test_parse_rss_guid_variations():
    # Test with empty guid
    rss_with_empty_guid = """
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>http://example.com</link>
            <item>
                <title>Test Item</title>
                <link>http://example.com/item1</link>
                <guid></guid>
            </item>
        </channel>
    </rss>
    """
    feed_info = parse_feed(rss_with_empty_guid)
    assert len(feed_info.items) == 1
    assert (
        feed_info.items[0].id == "http://example.com/item1"
    )  # Should fall back to link

    # Test with missing guid
    rss_without_guid = """
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>http://example.com</link>
            <item>
                <title>Test Item</title>
                <link>http://example.com/item2</link>
            </item>
        </channel>
    </rss>
    """
    feed_info = parse_feed(rss_without_guid)
    assert len(feed_info.items) == 1
    assert (
        feed_info.items[0].id == "http://example.com/item2"
    )  # Should fall back to link

    # Test with no guid and no link
    rss_without_guid_or_link = """
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>http://example.com</link>
            <item>
                <title>Test Item</title>
            </item>
        </channel>
    </rss>
    """
    feed_info = parse_feed(rss_without_guid_or_link)
    assert len(feed_info.items) == 1
    assert feed_info.items[0].id == ""  # Should be empty string when no guid or link


def test_parse_atom_id_variations():
    # Test with empty id
    atom_with_empty_id = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Test Feed</title>
        <link href="http://example.com"/>
        <entry>
            <title>Test Entry</title>
            <link href="http://example.com/entry1"/>
            <id></id>
        </entry>
    </feed>
    """
    feed_info = parse_feed(atom_with_empty_id)
    assert len(feed_info.items) == 1
    assert (
        feed_info.items[0].id == "http://example.com/entry1"
    )  # Should fall back to link

    # Test with missing id
    atom_without_id = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Test Feed</title>
        <link href="http://example.com"/>
        <entry>
            <title>Test Entry</title>
            <link href="http://example.com/entry2"/>
        </entry>
    </feed>
    """
    feed_info = parse_feed(atom_without_id)
    assert len(feed_info.items) == 1
    assert (
        feed_info.items[0].id == "http://example.com/entry2"
    )  # Should fall back to link

    # Test with no id and no link
    atom_without_id_or_link = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Test Feed</title>
        <link href="http://example.com"/>
        <entry>
            <title>Test Entry</title>
        </entry>
    </feed>
    """
    feed_info = parse_feed(atom_without_id_or_link)
    assert len(feed_info.items) == 1
    assert feed_info.items[0].id == ""  # Should be empty string when no id or link


@pytest.mark.asyncio
async def test_parse_feed_from_url():
    with aioresponses() as m:
        m.get("http://example.com/feed.xml", status=200, body=rss_data)

        feed_info = await parse_feed_from_url("http://example.com/feed.xml")
        assert isinstance(feed_info, FeedInfo)
        assert feed_info.title == "Example RSS Feed"
        assert feed_info.link == "https://example.com"
        assert len(feed_info.items) == 2
        assert feed_info.items[0].title == "RSS Item 1"


@pytest.mark.asyncio
async def test_parse_feed_from_url_with_params():
    headers = {"User-Agent": "TestBot/1.0"}
    timeout = 30.0

    with aioresponses() as m:
        m.get("http://example.com/feed.xml", status=200, body=rss_data, headers=headers)

        feed_info = await parse_feed_from_url(
            "http://example.com/feed.xml",
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        )
        assert isinstance(feed_info, FeedInfo)
        assert feed_info.title == "Example RSS Feed"


def test_parse_rss_without_guid():
    rss_content = """
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <link>http://example.com</link>
            <description>A test feed</description>
            <item>
                <title>Test Item</title>
                <link>http://example.com/item</link>
                <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """
    feed_info = parse_feed(rss_content)
    assert len(feed_info.items) == 1
    assert feed_info.items[0].id == "http://example.com/item"
