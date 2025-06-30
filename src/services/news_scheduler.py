from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

from src.dto.channel_dto import ChannelDTO
from src.services.channel_service import ChannelService
from src.services.message_service import MessageService
from src.services.news_source.news_source import NewsSource

class NewsScheduler:
    def __init__(self, channel_service: ChannelService, feed_service: NewsSource, message_service: MessageService):
        self.channel_service = channel_service
        self.feed_service = feed_service
        self.message_service = message_service
        self.scheduler = AsyncIOScheduler()
        self.loop = asyncio.get_event_loop()

    async def send_news_for_channel(self, channel: ChannelDTO):
        print(f"Отправка новостей для канала {channel.id}")
        await self.message_service.send_one_news_to_channel(channel, self.feed_service)

    async def schedule_all(self):
        channels = await self.channel_service.get_all_channels()
        for channel in channels:
            await self.schedule_channel(channel)

    async def schedule_channel(self, channel: ChannelDTO):
        interval = channel.work_interval_minutes
        self.scheduler.add_job(
            self._run_async_job,
            "interval",
            minutes=interval,
            args=[channel],
            id=f"news_job_{channel.id}",
            replace_existing=True
        )

    def start(self):
        self.scheduler.start()

    def remove_channel_job(self, channel_id: int):
        job_id = f"news_job_{channel_id}"
        self.scheduler.remove_job(job_id)
            
    def _run_async_job(self, channel):
        asyncio.run_coroutine_threadsafe(self.send_news_for_channel(channel), self.loop)
