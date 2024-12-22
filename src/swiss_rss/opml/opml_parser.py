from dataclasses import dataclass
from typing import List
import xml.etree.ElementTree as ET


@dataclass
class OpmlFeed:
    text: str
    title: str
    type: str
    xml_url: str
    html_url: str


def parse_opml(opml_content: str) -> List[OpmlFeed]:
    opml_content = opml_content.strip()
    root = ET.fromstring(opml_content)
    feeds = []

    for outline in root.findall(".//outline[@type='rss']"):
        feed = OpmlFeed(
            text=outline.get("text", ""),
            title=outline.get("title", ""),
            type=outline.get("type", ""),
            xml_url=outline.get("xmlUrl", ""),
            html_url=outline.get("htmlUrl", ""),
        )
        feeds.append(feed)

    return feeds
