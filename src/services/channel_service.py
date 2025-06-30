from src.domain.interfaces.channel_repository import IChannelRepository
from src.domain.entities import Channel
from src.dto.channel_dto import ChannelDTO

class ChannelService:
    def __init__(self, repository: IChannelRepository):
        self.repository = repository

    async def get_channel(self, channel_id: int) -> ChannelDTO | None:
        c = await self.repository.get_by_id(channel_id)
        if c is None:
            return
        return ChannelDTO(
            id=c.id,
            title=c.title,
            enabled=c.enabled,
            rss_links=c.rss_links,
            work_interval_minutes=c.work_interval_minutes
        )

    async def get_all_channels(self) -> list[ChannelDTO]:
        channels = await self.repository.get_all_channel()
        return [ChannelDTO(
                    id=c.id,
                    title=c.title, 
                    enabled=c.enabled, 
                    rss_links=c.rss_links, 
                    work_interval_minutes=c.work_interval_minutes
                ) for c in channels]

    async def register_channel(self, channel_dto: ChannelDTO):  
        channel = await self.repository.get_by_id(channel_dto.id)
        if channel is None:
            await self.repository.add_channel(Channel(
                id=channel_dto.id,
                title=channel_dto.title,
                enabled=True,
                rss_links=[],
                work_interval_minutes=1
            ))
            
    async def remove_channel(self, channel_id: int):
        await self.repository.del_channel(channel_id)

    async def set_title(self, channel_id: int, new_title: str) -> bool:
        return await self.repository.set_title(channel_id, new_title)

    async def add_rss(self, channel_id: int, rss_url: str) -> bool:
        channel = await self.repository.get_by_id(channel_id)
        if channel and rss_url not in channel.rss_links:
            return await self.repository.add_rss(channel_id, rss_url)
        return False

    async def remove_rss(self, channel_id: int, rss_url: str) -> bool:
        return await self.repository.remove_rss(channel_id, rss_url)

    async def set_enabled(self, channel_id: int):
        return await self.repository.set_enabled(channel_id)
    
    async def set_disable(self, channel_id: int):
        return await self.repository.set_disable(channel_id)

    async def set_work_interval(self, channel_id: int, interval_minutes: int):
        if interval_minutes < 5:
            raise RuntimeError("Min time interval cannot be less than 5 min")
        return await self.repository.set_work_interval(channel_id, interval_minutes)

    async def get_work_interval(self, channel_id: int) -> int:
        return await self.repository.get_work_interval(channel_id)

    async def add_last_sent_links(self, channel_id: int, link: str):
        await self.repository.add_last_news_link(channel_id, link)
        
    async def get_last_sent_links(self, channel_id: int) -> list[str | None]:
        return await self.repository.get_last_news_sent_links(channel_id)
