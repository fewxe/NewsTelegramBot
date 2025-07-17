from importlib.metadata import distribution
import feedparser
from typing import cast
from feedparser.util import FeedParserDict
from bs4 import BeautifulSoup, Tag
import aiohttp

from src.domain.entities import News
from src.services.news_source.news_source import NewsSource
from src.logging_config import logger


logger = logger.getChild(__name__)


class FeedService(NewsSource):
    async def fetch_latest_news(self, feed_url: str) -> list[News]:
        logger.info(f"Fetching feed: {feed_url}")
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            logger.warning(f"Feed parse error for {feed_url}: {feed.bozo_exception}")

        entries = feed.entries
        if not entries:
            logger.info(f"No entries found for feed: {feed_url}")

        news_list = []
        async with aiohttp.ClientSession() as session:
            for entry in entries:
                if not self._is_valid_entry(entry):
                    logger.debug(f"Invalid entry skipped: {entry}")
                    continue
                news = await self._parse_entry(entry, session)
                news_list.append(news)

        logger.info(f"Fetched {len(news_list)} valid news items from: {feed_url}")
        return news_list

    def _is_valid_entry(self, entry: FeedParserDict) -> bool:
        title = entry.get('title')
        link = entry.get('link')
        description = entry.get('description')
        is_valid = all(isinstance(field, str) for field in [title, link, description])
        if not is_valid:
            logger.debug(
                f"Entry validation failed. title={title}, link={link}, description={description}"
            )
        return is_valid

    async def _parse_entry(self, entry, session: aiohttp.ClientSession) -> News:
        title = cast(str, entry.get('title'))
        link = cast(str, entry.get('link'))
        description = cast(str, entry.get('description'))

        logger.debug(f"Parsing entry: title='{title}', link='{link}'")

        text, img_url = self._parse_description(description)

        if img_url:
            logger.debug(f"Found image URL in description: {img_url}")

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
                    logger.debug(f"Image downloaded successfully: {img_url}")
                    return await response.read()
                else:
                    logger.warning(f"Image download failed with status {response.status}: {img_url}")
        except Exception as e:
            logger.warning(f"Error downloading image {img_url}: {e}")
        return None
