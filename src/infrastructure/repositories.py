from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.models import ChannelModel
from src.domain.entities import Channel
from src.domain.interfaces.channel_repository import IChannelRepository
from src.logging_config import logger

logger = logger.getChild(__name__)


class ChannelRepository(IChannelRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, channel_id: int) -> Channel | None:
        try:
            result = await self.session.execute(
                select(ChannelModel).where(ChannelModel.id == channel_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                logger.debug(f"Channel not found: {channel_id}")
                return None

            return Channel(
                id=model.id,
                title=model.title,
                rss_links=list(model.rss_links),
                enabled=model.enabled,
                work_interval_minutes=model.work_interval_minutes,
            )
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def get_all_channel(self) -> list[Channel]:
        try:
            result = await self.session.execute(select(ChannelModel))
            models = result.scalars().all()
            return [
                Channel(
                    id=m.id,
                    title=m.title,
                    rss_links=list(m.rss_links),
                    enabled=m.enabled,
                    work_interval_minutes=m.work_interval_minutes,
                )
                for m in models
            ]
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def add_channel(self, channel: Channel) -> None:
        try:
            model = ChannelModel(
                id=channel.id,
                title=channel.title,
                rss_links=channel.rss_links,
                enabled=channel.enabled,
                work_interval_minutes=channel.work_interval_minutes,
            )
            self.session.add(model)
            await self.session.commit()
            logger.info(f"Channel created: {channel.id}")
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def del_channel(self, channel_id: int):
        try:
            result = await self.session.execute(
                select(ChannelModel).where(ChannelModel.id == channel_id)
            )
            model = result.scalar_one_or_none()
            if model:
                await self.session.delete(model)
                await self.session.commit()
                logger.info(f"Channel deleted: {channel_id}")
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def set_title(self, channel_id: int, new_title: str) -> bool:
        try:
            result = await self.session.execute(
                select(ChannelModel).where(ChannelModel.id == channel_id)
            )
            model = result.scalar_one_or_none()
            if model:
                model.title = new_title
                await self.session.commit()
                logger.debug(f"Channel title updated: {channel_id} -> {new_title}")
                return True
            logger.debug(f"Channel not found for title update: {channel_id}")
            return False
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def add_rss(self, channel_id: int, rss_url: str) -> bool:
        try:
            result = await self.session.execute(
                select(ChannelModel).where(ChannelModel.id == channel_id)
            )
            model = result.scalar_one_or_none()
            if model and rss_url not in model.rss_links:
                model.rss_links.append(rss_url)
                flag_modified(model, "rss_links")
                await self.session.commit()
                logger.debug(f"RSS added: {rss_url} -> {channel_id}")
                return True
            logger.debug(f"Failed to add RSS: {rss_url} -> {channel_id}")
            return False
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def remove_rss(self, channel_id: int, rss_url: str) -> bool:
        try:
            result = await self.session.execute(
                select(ChannelModel).where(ChannelModel.id == channel_id)
            )
            model = result.scalar_one_or_none()
            if model and rss_url in model.rss_links:
                model.rss_links.remove(rss_url)
                flag_modified(model, "rss_links")
                await self.session.commit()
                logger.debug(f"RSS removed: {rss_url} <- {channel_id}")
                return True
            logger.debug(f"Failed to remove RSS: {rss_url} <- {channel_id}")
            return False
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def set_enabled(self, channel_id: int):
        try:
            await self.session.execute(
                update(ChannelModel)
                .where(ChannelModel.id == channel_id)
                .values(enabled=True)
            )
            await self.session.commit()
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def set_disable(self, channel_id: int):
        try:
            await self.session.execute(
                update(ChannelModel)
                .where(ChannelModel.id == channel_id)
                .values(enabled=False)
            )
            await self.session.commit()
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def set_work_interval(self, channel_id: int, interval_minutes: int):
        try:
            await self.session.execute(
                update(ChannelModel)
                .where(ChannelModel.id == channel_id)
                .values(work_interval_minutes=interval_minutes)
            )
            await self.session.commit()
        except SQLAlchemyError:
            logger.exception(f"Database error on set_work_interval({channel_id})")
            raise


    async def get_work_interval(self, channel_id: int) -> int:
        try:
            result = await self.session.execute(
                select(ChannelModel.work_interval_minutes).where(ChannelModel.id == channel_id)
            )
            interval = result.scalar_one_or_none()
            if interval is None:
                logger.debug(f"No interval found for channel id={channel_id}")
                return 0
            return interval
        except SQLAlchemyError:
            logger.exception(f"DB error on get_work_interval({channel_id})")
            raise

    async def add_last_news_link(self, channel_id: int, link: str, max_links: int = 200):
        try:
            result = await self.session.execute(
                select(ChannelModel).where(ChannelModel.id == channel_id)
            )
            model = result.scalar_one_or_none()
            if model:
                sent_links = list(model.last_sent_links) if model.last_sent_links else []
                sent_links.append(link)
                sent_links = sent_links[-max_links:]
                model.last_sent_links = sent_links
                flag_modified(model, "last_sent_links")
                await self.session.commit()
                logger.debug(f"Last news link added: {link} -> {channel_id}")
        except SQLAlchemyError:
            logger.exception("Database error")
            raise

    async def get_last_news_sent_links(self, channel_id: int) -> list[str | None]:
        try:
            result = await self.session.execute(
                select(ChannelModel.last_sent_links).where(ChannelModel.id == channel_id)
            )
            links = result.scalar_one_or_none()
            return links if links else []
        except SQLAlchemyError:
            logger.exception(f"Database error on get_last_news_sent_links({channel_id})")
            raise

