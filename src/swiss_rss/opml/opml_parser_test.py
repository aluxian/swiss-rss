from .opml_parser import OpmlFeed, parse_opml


def test_parse_opml():
    sample_opml = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <head>
    <title>Feeds of Alexandru Rosianu from Inoreader [https://www.inoreader.com]</title>
  </head>
  <body>
    <outline text="@visakanv" title="@visakanv" type="rss" xmlUrl="https://www.visakanv.com/archives/feed/" htmlUrl="https://www.visakanv.com/archives"/>
    <outline text="2ality" title="2ality" type="rss" xmlUrl="https://2ality.com/feeds/posts.atom" htmlUrl="https://2ality.com/"/>
    <outline text="A Smart Bear" title="A Smart Bear" type="rss" xmlUrl="https://longform.asmartbear.com/index.xml" htmlUrl="https://longform.asmartbear.com/"/>
  </body>
</opml>
"""

    feeds = parse_opml(sample_opml)

    assert len(feeds) == 3
    assert feeds[0] == OpmlFeed(
        text="@visakanv",
        title="@visakanv",
        type="rss",
        xml_url="https://www.visakanv.com/archives/feed/",
        html_url="https://www.visakanv.com/archives",
    )
    assert feeds[1] == OpmlFeed(
        text="2ality",
        title="2ality",
        type="rss",
        xml_url="https://2ality.com/feeds/posts.atom",
        html_url="https://2ality.com/",
    )
    assert feeds[2] == OpmlFeed(
        text="A Smart Bear",
        title="A Smart Bear",
        type="rss",
        xml_url="https://longform.asmartbear.com/index.xml",
        html_url="https://longform.asmartbear.com/",
    )
