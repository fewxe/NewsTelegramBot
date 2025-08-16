from src.domain.interfaces.channel_repository import IChannelRepository
from src.domain.entities import Channel
from src.dto.channel_dto import ChannelDTO
from src.logging_config import logger


logger = logger.getChild(__name__)

class ChannelService:
    def __init__(self, repository: IChannelRepository):
        self.repository = repository

    async def get_channel(self, channel_id: int) -> ChannelDTO | None:
        c = await self.repository.get_by_id(channel_id)
        if c is None:
            logger.debug(f"Channel with id={channel_id} not found")
            return None
        logger.debug(f"Channel with id={channel_id} found")
        return ChannelDTO(
            id=c.id,
            title=c.title,
            enabled=c.enabled,
            rss_links=c.rss_links,
            work_interval_minutes=c.work_interval_minutes
        )

    async def get_all_channels(self) -> list[ChannelDTO]:
        channels = await self.repository.get_all_channel()
        logger.debug(f"Retrieved {len(channels)} channels")
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
            logger.info(f"New channel registered with id={channel_dto.id}")
        else:
            logger.debug(f"Channel with id={channel_dto.id} already exists, skipping registration")

    async def remove_channel(self, channel_id: int):
        await self.repository.del_channel(channel_id)
        logger.info(f"Channel with id={channel_id} removed")

    async def set_title(self, channel_id: int, new_title: str) -> bool:
        updated = await self.repository.set_title(channel_id, new_title)
        if updated:
            logger.info(f"Channel title updated for id={channel_id} to '{new_title}'")
        else:
            logger.warning(f"Failed to update title: channel with id={channel_id} not found")
        return updated

    async def add_rss(self, channel_id: int, rss_url: str) -> bool:
        channel = await self.repository.get_by_id(channel_id)
        if channel and rss_url not in channel.rss_links:
            added = await self.repository.add_rss(channel_id, rss_url)
            if added:
                logger.info(f"RSS '{rss_url}' added to channel id={channel_id}")
            else:
                logger.warning(f"Failed to add RSS '{rss_url}' to channel id={channel_id}")
            return added
        logger.warning(f"RSS '{rss_url}' already exists or channel id={channel_id} not found")
        return False

    async def remove_rss(self, channel_id: int, rss_url: str) -> bool:
        removed = await self.repository.remove_rss(channel_id, rss_url)
        if removed:
            logger.info(f"RSS '{rss_url}' removed from channel id={channel_id}")
        else:
            logger.warning(f"Failed to remove RSS '{rss_url}' from channel id={channel_id}")
        return removed

    async def set_enabled(self, channel_id: int):
        await self.repository.set_enabled(channel_id)
        logger.info(f"Channel with id={channel_id} enabled")
    
    async def set_disable(self, channel_id: int):
        await self.repository.set_disable(channel_id)
        logger.info(f"Channel with id={channel_id} disabled")

    async def set_work_interval(self, channel_id: int, interval_minutes: int):
        if interval_minutes <= 1:
            logger.error(f"Attempted to set interval less than 1 minutes for channel id={channel_id}")
            raise RuntimeError("Min time interval cannot be less than 1 min")
        await self.repository.set_work_interval(channel_id, interval_minutes)
        logger.info(f"Interval set to {interval_minutes} minutes for channel id={channel_id}")

    async def get_work_interval(self, channel_id: int) -> int:
        interval = await self.repository.get_work_interval(channel_id)
        logger.debug(f"Retrieved interval {interval} minutes for channel id={channel_id}")
        return interval

    async def add_last_sent_links(self, channel_id: int, link: str):
        await self.repository.add_last_news_link(channel_id, link)
        logger.debug(f"Added news link to history for channel id={channel_id}")

    async def get_last_sent_links(self, channel_id: int) -> list[str | None]:
        links = await self.repository.get_last_news_sent_links(channel_id)
        logger.debug(f"Retrieved sent links history for channel id={channel_id} ({len(links)} links)")
        return links
