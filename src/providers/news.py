"""News provider: Google News RSS feeds."""

import re
import html
import urllib.request
from xml.etree import ElementTree
from . import NewsProvider, NewsSection, NewsItem, register


RSS_FEEDS: dict[str, str] = {
    "AI & Tecnologia": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FuUjVHZ0pWVXlnQVAB?hl=es-419&gl=AR&ceid=AR:es-419",
    "Mercados & Finanzas": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FuUjVHZ0pTV3lnQVAB?hl=es-419&gl=AR&ceid=AR:es-419",
    "Politica & Global": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FuUjVHZ0pWVXlnQVAB?hl=es-419&gl=AR&ceid=AR:es-419",
    "Ciencia & Salud": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxY0d3U0FuUjVHZ0pWVXlnQVAB?hl=es-419&gl=AR&ceid=AR:es-419",
    "Startups & Negocios": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxY1R3U0FuUjVHZ0pWVXlnQVAB?hl=es-419&gl=AR&ceid=AR:es-419",
    "Desarrollo & Tech": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxY0RRU0FuUjVHZ0pWVXlnQVAB?hl=es-419&gl=AR&ceid=AR:es-419",
}


class GoogleNewsRSS(NewsProvider):
    def __init__(self, feeds: dict[str, str] | None = None,
                 max_per_section: int = 5):
        self.feeds = feeds or RSS_FEEDS
        self.max_per_section = max_per_section

    def is_available(self) -> bool:
        return True

    def _fetch_feed(self, url: str) -> list[NewsItem]:
        """Parse Google News RSS → list of NewsItem."""
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = resp.read()
                # Google News RSS sometimes has encoding issues — force UTF-8
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    text = raw.decode("latin-1")
                text = re.sub(r'^<\?xml[^>]*\?>', '', text)
                root = ElementTree.fromstring(text.encode("utf-8"))
                items = []
                for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                    title_el = entry.find("{http://www.w3.org/2005/Atom}title")
                    link_el = entry.find("{http://www.w3.org/2005/Atom}link")
                    source_el = entry.find("{http://www.w3.org/2005/Atom}source")
                    if title_el is not None and link_el is not None:
                        title = html.unescape(title_el.text or "").strip()
                        href = link_el.attrib.get("href", "")
                        source = ""
                        if source_el is not None:
                            src_title = source_el.find("{http://www.w3.org/2005/Atom}title")
                            if src_title is not None:
                                source = html.unescape(src_title.text or "")
                        items.append(NewsItem(title=title, url=href, source=source))
                return items[:self.max_per_section]
        except Exception:
            return []

    def get_headlines(self, sections: list[str] | None = None) -> list[NewsSection]:
        sections = sections or list(self.feeds.keys())
        result = []
        for name in sections:
            feed_url = self.feeds.get(name)
            if not feed_url:
                continue
            items = self._fetch_feed(feed_url)
            if items:
                result.append(NewsSection(name=name, items=items))
        return result


register(GoogleNewsRSS)
