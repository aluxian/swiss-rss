import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from loguru import logger

from .timestamps import parse_date


@dataclass
class FeedItem:
    """Represents a single item/entry in an RSS/Atom feed.

    Attributes:
        title: The title of the feed item
        link: The URL link to the full content
        guid: Globally unique identifier for the item (required for database)
        description: Optional summary or description of the content
        pub_date: Optional publication date
        id: Optional ID (defaults to guid value)
        author: Optional author name
    """

    title: str
    link: str
    guid: str  # Required field for database
    description: Optional[str] = None
    pub_date: Optional[datetime] = None
    id: Optional[str] = None
    author: Optional[str] = None


@dataclass
class FeedInfo:
    """Represents a parsed RSS/Atom feed.

    Attributes:
        title: The title of the feed
        link: The URL of the feed's website
        items: List of FeedItem objects containing the feed entries
        description: Optional description of the feed
    """

    title: str
    link: str
    items: List[FeedItem]
    description: Optional[str] = None


def parse_feed(feed_content: str) -> FeedInfo:
    """Parse RSS/Atom feed content into a FeedInfo object.

    Args:
        feed_content: The XML content of the RSS/Atom feed

    Returns:
        FeedInfo object containing the parsed feed data

    Raises:
        ValueError: If the feed format is unsupported or invalid
    """
    feed_content = feed_content.strip()
    try:
        root = ET.fromstring(feed_content)
        if root.tag.endswith("rss"):
            return _parse_rss(root)
        elif root.tag.endswith("feed"):
            return _parse_atom(root)
        else:
            raise ValueError("Unsupported feed format")
    except ET.ParseError as e:
        raise ValueError(f"Invalid feed XML: {str(e)}")


async def discover_feed(
    url: str, session: Optional[aiohttp.ClientSession] = None
) -> Optional[str]:
    """
    Try to find a feed URL from a webpage.
    Returns the feed URL if found, None otherwise.
    """

    async def _discover(client_session):
        try:
            async with client_session.get(url) as response:
                if response.status != 200:
                    return None

                content = await response.text()
                soup = BeautifulSoup(content, "lxml-xml")

                # Look for RSS/Atom feed links
                feed_links = []

                # Check link tags
                for link in soup.find_all("link"):
                    type_attr = link.get("type", "").lower()
                    if type_attr in ["application/rss+xml", "application/atom+xml"]:
                        href = link.get("href")
                        if href:
                            feed_links.append(href)

                # Check a tags
                for a in soup.find_all("a"):
                    href = a.get("href", "").lower()
                    if any(x in href for x in ["rss", "feed", "atom"]):
                        feed_links.append(a["href"])

                if not feed_links:
                    return None

                # Convert relative URLs to absolute
                from urllib.parse import urljoin

                base_url = str(response.url)
                feed_links = [urljoin(base_url, link) for link in feed_links]

                # Try each feed link until we find a valid one
                for feed_url in feed_links:
                    try:
                        # Ensure URL is valid
                        feed_url = str(feed_url).strip()
                        if not feed_url:
                            continue

                        async with client_session.get(feed_url) as feed_response:
                            if feed_response.status != 200:
                                continue

                            feed_content = await feed_response.text()
                            # Verify it's a valid feed by trying to parse it
                            parse_feed(feed_content)
                            return str(feed_url)
                    except Exception as e:
                        logger.debug(f"Failed to validate feed {feed_url}: {str(e)}")
                        continue

                return None

        except Exception as e:
            logger.error(f"Error discovering feed from {url}: {str(e)}")
            return None

    if session:
        return await _discover(session)

    async with aiohttp.ClientSession() as new_session:
        return await _discover(new_session)


def _parse_rss(root: ET.Element) -> FeedInfo:
    """Parse an RSS feed from an XML Element.

    Args:
        root: The root XML Element of the RSS feed

    Returns:
        FeedInfo object containing the parsed RSS feed data

    Raises:
        ValueError: If required RSS elements are missing
    """
    channel = root.find("channel")
    if channel is None:
        raise ValueError("missing channel element in RSS feed")

    info = FeedInfo(
        title=channel.findtext("title", ""),
        link=channel.findtext("link", ""),
        description=channel.findtext("description"),
        items=[],
    )

    for item in channel.findall("item"):
        link = item.findtext("link", "")
        # Use guid if present and non-empty, otherwise use link
        guid = item.findtext("guid", "").strip() or link or ""
        feed_item = FeedItem(
            title=item.findtext("title", ""),
            link=link,
            guid=guid,
            description=item.findtext("description"),
            pub_date=parse_date(item.findtext("pubDate")),
            id=guid,  # Always use same value as guid
            author=item.findtext("author"),
        )
        info.items.append(feed_item)

    return info


async def parse_feed_from_url(
    url: str,
    session: Optional[ClientSession] = None,
    *,
    headers: Optional[dict] = None,
    timeout: Optional[float] = None,
    **kwargs,
) -> FeedInfo:
    """Download and parse a feed from a URL.

    Args:
        url: The URL of the RSS/Atom feed
        session: Optional aiohttp ClientSession to use for the request
        headers: Optional headers to send with the request
        timeout: Optional timeout in seconds
        **kwargs: Additional arguments to pass to aiohttp.ClientSession.get()

    Returns:
        FeedInfo object containing the parsed feed data

    Raises:
        aiohttp.ClientError: If the HTTP request fails
        ValueError: If the feed format is unsupported or invalid
    """

    async def _parse(client_session):
        async with client_session.get(
            url, headers=headers, timeout=timeout, **kwargs
        ) as response:
            response.raise_for_status()
            content = await response.text()
            return parse_feed(content)

    if session:
        return await _parse(session)

    async with aiohttp.ClientSession() as new_session:
        return await _parse(new_session)


def _parse_atom(root: ET.Element) -> FeedInfo:
    """Parse an Atom feed from an XML Element.

    Args:
        root: The root XML Element of the Atom feed

    Returns:
        FeedInfo object containing the parsed Atom feed data
    """
    link = ""
    link_elem = root.find("{http://www.w3.org/2005/Atom}link")
    if link_elem is not None:
        link = link_elem.get("href", "")

    info = FeedInfo(
        title=root.findtext("{http://www.w3.org/2005/Atom}title", ""),
        link=link,
        description=root.findtext("{http://www.w3.org/2005/Atom}subtitle"),
        items=[],
    )

    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        link = ""
        link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
        if link_elem is not None:
            link = link_elem.get("href", "")

        # Use id if present and non-empty, otherwise use link
        guid = (
            entry.findtext("{http://www.w3.org/2005/Atom}id", "").strip() or link or ""
        )

        author = entry.find(
            "{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name"
        )
        author_text = author.text if author is not None else None

        feed_item = FeedItem(
            title=entry.findtext("{http://www.w3.org/2005/Atom}title", ""),
            link=link,
            guid=guid,
            description=entry.findtext("{http://www.w3.org/2005/Atom}summary"),
            pub_date=parse_date(
                entry.findtext("{http://www.w3.org/2005/Atom}published")
            ),
            author=author_text,
            id=guid,  # Always use same value as guid
        )
        info.items.append(feed_item)

    return info
