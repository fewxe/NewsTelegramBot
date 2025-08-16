from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

from src.dto.channel_dto import ChannelDTO
from src.services.channel_service import ChannelService
from src.services.message_service import MessageService
from src.services.news_source.news_source import NewsSource
from src.logging_config import logger


logger = logger.getChild(__name__)

class NewsScheduler:
    def __init__(self, channel_service: ChannelService, feed_service: NewsSource, message_service: MessageService):
        self.channel_service = channel_service
        self.feed_service = feed_service
        self.message_service = message_service
        self.scheduler = AsyncIOScheduler()
        self.loop = asyncio.get_event_loop()

    async def send_news_for_channel(self, channel: ChannelDTO):
        try:
            await self.message_service.send_one_news_to_channel(channel, self.feed_service)
        except Exception:
            logger.exception(f"Failed to send news for channel ID={channel.id}")

    async def schedule_all(self):
        try:
            channels = await self.channel_service.get_all_channels()
            for channel in channels:
                await self.schedule_channel(channel)
        except Exception:
            logger.exception("Failed to schedule all channels")

    async def schedule_channel(self, channel: ChannelDTO):
        try:
            self.scheduler.add_job(
                self._run_async_job,
                "interval",
                minutes=channel.work_interval_minutes,
                args=[channel],
                id=f"news_job_{channel.id}",
                replace_existing=True
            )
        except Exception:
            logger.exception(f"Failed to schedule job for channel ID={channel.id}")

    def start(self):
        logger.info("Starting news scheduler")
        try:
            self.scheduler.start()
        except Exception:
            logger.critical("Failed to start news scheduler", exc_info=True)

    def remove_channel_job(self, channel_id: int):
        job_id = f"news_job_{channel_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job for channel ID={channel_id}")
        except Exception:
            logger.warning(f"Failed to remove job for channel ID={channel_id}", exc_info=True)

    def _run_async_job(self, channel: ChannelDTO):
        try:
            asyncio.run_coroutine_threadsafe(self.send_news_for_channel(channel), self.loop)
        except Exception:
            logger.critical(f"Failed to run async job for channel ID={channel.id}", exc_info=True)
