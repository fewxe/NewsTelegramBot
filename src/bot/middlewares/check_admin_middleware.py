from collections.abc import Callable
import time
from typing import Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineQuery
from aiogram.exceptions import TelegramAPIError
from src.services.channel_service import ChannelService
from src.logging_config import logger

logger = logger.getChild(__name__)

class AdminCheckMiddleware(BaseMiddleware):
    def __init__(self, bot, channel_service: ChannelService):
        super().__init__()
        self.bot = bot
        self.channel_service = channel_service
        self.channel_admins: dict[int, set[int]] = {}
        self.last_update_time = 0
        self.cache_ttl = 300

    async def update_admins(self):
        try:
            channels = await self.channel_service.get_all_channels()
            new_channel_admins = {}
            for channel in channels:
                channel_id = channel.id
                try:
                    admins = await self.bot.get_chat_administrators(channel_id)
                    admin_ids = {admin.user.id for admin in admins}
                    new_channel_admins[channel_id] = admin_ids
                    logger.info(f"Updated admins for channel {channel_id}: {admin_ids}")
                except TelegramAPIError as e:
                    logger.error(f"Failed to get admins for channel {channel_id}: {e}")
                    continue
                except Exception as e:
                    logger.exception(f"Unexpected error for channel {channel_id}: {e}")
                    continue
            self.channel_admins = new_channel_admins
            self.last_update_time = time.time()
            logger.info(f"Admin cache updated: {len(new_channel_admins)} channels")
        except Exception as e:
            logger.exception("Failed to update channel admins")

    def get_all_admin_ids(self) -> set[int]:
        all_ids = set()
        for ids in self.channel_admins.values():
            all_ids.update(ids)
        return all_ids

    async def is_admin(self, user_id: int) -> bool:
        now = time.time()
        if (now - self.last_update_time) > self.cache_ttl or not self.channel_admins:
            await self.update_admins()
        is_admin = user_id in self.get_all_admin_ids()
        return is_admin

    def _get_user_from_event(self, event: TelegramObject) -> int | None:
        if not isinstance(event, (Message, CallbackQuery, InlineQuery)):
            return
        return event.from_user.id if event.from_user is not None else None

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Any],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        user_id = self._get_user_from_event(event)
        if user_id is None:
            return await handler(event, data)

        if not await self.is_admin(user_id):
            logger.info(f"User {user_id} is not an admin. Event {type(event)} ignored.")
            return None

        return await handler(event, data)
