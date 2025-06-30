from src.services.channel_service import ChannelService
from src.services.news_scheduler import NewsScheduler
from src.dto.channel_dto import ChannelDTO


class ChannelManager:
    def __init__(self, channel_service: ChannelService, news_scheduler: NewsScheduler):
        self.channel_service = channel_service
        self.news_scheduler = news_scheduler

    async def add_channel(self, channel_dto: ChannelDTO):
        await self.channel_service.register_channel(channel_dto)
        channel = await self.channel_service.get_channel(channel_dto.id)
        if channel:
            await self.news_scheduler.schedule_channel(channel)

    async def remove_channel(self, channel_id: int):
        await self.channel_service.remove_channel(channel_id)
        self.news_scheduler.remove_channel_job(channel_id)

    async def update_channel(self, channel_id: int):
        channel = await self.channel_service.get_channel(channel_id)
        if channel:
            await self.news_scheduler.schedule_channel(channel)

    async def add_rss(self, channel_id: int, rss_url: str):
        ok = await self.channel_service.add_rss(channel_id, rss_url)
        if ok:
            await self.update_channel(channel_id)
        return ok

    async def remove_rss(self, channel_id: int, rss_url: str):
        ok = await self.channel_service.remove_rss(channel_id, rss_url)
        if ok:
            await self.update_channel(channel_id)

    async def set_work_interval(self, channel_id: int, interval_minutes: int):
        await self.channel_service.set_work_interval(channel_id, interval_minutes)
        await self.update_channel(channel_id)

    async def enable_channel(self, channel_id: int):
        await self.channel_service.set_enabled(channel_id)
        await self.update_channel(channel_id)

    async def disable_channel(self, channel_id: int):
        await self.channel_service.set_disable(channel_id)
        await self.update_channel(channel_id)
