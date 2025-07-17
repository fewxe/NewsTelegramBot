from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from src.dto.channel_dto import ChannelDTO
from src.services.channel_service import ChannelService
from src.logging_config import logger


logger = logger.getChild(__name__)

def channel_events_router(bot: Bot, channel_service: ChannelService) -> Router:
    router = Router()

    @router.my_chat_member()
    async def on_added_to_channel(event: ChatMemberUpdated):
        if event.new_chat_member.status in ("administrator", "member") and event.chat.type == "channel":
            logger.info(f"Бот добавлен в канал {event.chat.id} ({event.chat.title})")
            await channel_service.register_channel(ChannelDTO(
                    event.chat.id,
                    event.chat.title or f"Канал {event.chat.id}",
                    False,
                    [],
                    1
                )
            )
            await bot.send_message(
                event.chat.id,
                "Бот успешно добавлен как администратор в этот канал!"
            )

    return router
