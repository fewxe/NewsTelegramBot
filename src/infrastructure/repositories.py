from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm.attributes import flag_modified

from src.infrastructure.models import ChannelModel
from src.domain.entities import Channel
from src.domain.interfaces.channel_repository import IChannelRepository


class ChannelRepository(IChannelRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, channel_id: int) -> Channel | None:
        result = await self.session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return Channel(
                id=model.id,
                title=model.title,
                rss_links=list(model.rss_links),
                enabled=model.enabled,
                work_interval_minutes=model.work_interval_minutes,
            )

    async def get_all_channel(self) -> list[Channel]:
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

    async def add_channel(self, channel: Channel) -> None:
        model = ChannelModel(
            id=channel.id,
            title=channel.title,
            rss_links=channel.rss_links,
            enabled=channel.enabled,
            work_interval_minutes=channel.work_interval_minutes,
        )
        self.session.add(model)
        await self.session.commit()
        
    async def del_channel(self, channel_id: int):
        result = await self.session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.commit()

    async def set_title(self, channel_id: int, new_title: str) -> bool:
        result = await self.session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.title = new_title
            await self.session.commit()
            return True
        return False

    async def add_rss(self, channel_id: int, rss_url: str) -> bool:
        result = await self.session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        if model and rss_url not in model.rss_links:
            model.rss_links.append(rss_url)
            flag_modified(model, "rss_links")
            await self.session.commit()
            return True
        return False

    async def remove_rss(self, channel_id: int, rss_url: str) -> bool:
        result = await self.session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        if model and rss_url in model.rss_links:
            model.rss_links.remove(rss_url)
            flag_modified(model, "rss_links")
            await self.session.commit()
            return True
        return False

    async def set_enabled(self, channel_id: int):
        await self.session.execute(
            update(ChannelModel)
            .where(ChannelModel.id == channel_id)
            .values(enabled=True)
        )
        await self.session.commit()

    async def set_disable(self, channel_id: int):
        await self.session.execute(
            update(ChannelModel)
            .where(ChannelModel.id == channel_id)
            .values(enabled=False)
        )
        await self.session.commit()

    async def set_work_interval(self, channel_id: int, interval_minutes: int):
        result = await self.session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.work_interval_minutes = interval_minutes
            await self.session.commit()

    async def get_work_interval(self, channel_id: int) -> int:
        result = await self.session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        return model.work_interval_minutes if model else 0

    async def add_last_news_link(self, channel_id: int, link: str, max_links: int = 200):
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

    async def get_last_news_sent_links(self, channel_id: int) -> list[str | None]:
        result = await self.session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return []
        return model.last_sent_links
