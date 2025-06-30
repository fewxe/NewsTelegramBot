from importlib.metadata import distribution
import feedparser
from typing import cast
from feedparser.util import FeedParserDict
from bs4 import BeautifulSoup, Tag
import aiohttp

from src.domain.entities import News
from src.services.news_source.news_source import NewsSource


class FeedService(NewsSource):

    async def fetch_latest_news(self, feed_url: str) -> list[News]:
        feed = feedparser.parse(feed_url)
        entries = feed.entries
        async with aiohttp.ClientSession() as session:
            return [await self._parse_entry(entry, session) for entry in entries if self._is_valid_entry(entry)]

    def _is_valid_entry(self, entry) -> bool:
        if not isinstance(entry, FeedParserDict):
            return False
        title = entry.get('title')
        link = entry.get('link')
        description = entry.get('description')
        return all(isinstance(field, str) for field in [title, link, description])

    async def _parse_entry(self, entry, session: aiohttp.ClientSession) -> News:
        title = cast(str, entry.get('title'))
        link = cast(str, entry.get('link'))
        description = cast(str, entry.get('description'))

        text, img_url = self._parse_description(description)
        image_bytes = await self._download_image(img_url, session) if img_url else None

        return News(
            title=title,
            link=link,
            description=text,
            image_link=image_bytes
        )

    def _parse_description(self, description: str) -> tuple[str, str | None]:
        soup = BeautifulSoup(description, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        img_tag = soup.find("img")
        img_url = img_tag.get("src") if isinstance(img_tag, Tag) else None
        if not isinstance(img_url, str):
            img_url = None
        return text, img_url

    async def _download_image(self, img_url: str, session: aiohttp.ClientSession) -> bytes | None:
        try:
            async with session.get(img_url, timeout=5) as response:
                if response.status == 200:
                    return await response.read()
        except Exception as e:
            print(f"Ошибка при скачивании изображения: {e}")
        return None
