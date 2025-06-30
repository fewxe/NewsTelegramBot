from abc import ABC, abstractmethod
from src.domain.entities import Channel

class IChannelRepository(ABC):
    @abstractmethod
    async def get_by_id(self, channel_id: int) -> Channel | None:
        ...

    @abstractmethod
    async def get_all_channel(self) -> list[Channel]:
        ...

    @abstractmethod
    async def add_channel(self, channel: Channel) -> None:
        ...
        
    @abstractmethod
    async def del_channel(self, channel_id: int) -> None:
        ...

    @abstractmethod
    async def set_title(self, channel_id: int, new_title: str) -> bool:
        ...

    @abstractmethod
    async def add_rss(self, channel_id: int, rss_url: str) -> bool:
        ...

    @abstractmethod
    async def remove_rss(self, channel_id: int, rss_url: str) -> bool:
        ...

    @abstractmethod
    async def set_enabled(self, channel_id: int):
        ...
    
    @abstractmethod
    async def set_disable(self, channel_id: int):
        ...

    @abstractmethod
    async def set_work_interval(self, channel_id: int, interval_minutes: int):
        ...

    @abstractmethod
    async def get_work_interval(self, channel_id: int) -> int:
        ...

    @abstractmethod
    async def add_last_news_link(self, channel_id: int, link: str):
        ...

    @abstractmethod
    async def get_last_news_sent_links(self, channel_id: int) -> list[str | None]:
        ...
