from abc import ABC, abstractmethod

from src.domain.entities import News


class NewsSource(ABC):
    @abstractmethod
    async def fetch_latest_news(self, feed_url: str) -> list[News]:
        pass
            