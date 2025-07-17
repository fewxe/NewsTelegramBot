from aiogram import Bot
from aiogram.types import InputFile, BufferedInputFile
from src.services.interfaces.message_sender import IMessageSender
from src.logging_config import logger


logger = logger.getChild(__name__)


class TelegramMessageSender(IMessageSender):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_message(self, chat_id: int, text: str, attachments: bytes | None = None) -> None:
        try:
            if attachments:
                photo = BufferedInputFile(attachments, filename="image.jpg")
                await self.bot.send_photo(chat_id, photo=photo, caption=text)
                logger.info(f"Отправлено изображение в чат {chat_id}, размер: {len(attachments)} байт")
            else:
                await self.bot.send_message(chat_id, text)
                logger.info(f"Отправлено текстовое сообщение в чат {chat_id}")
        except Exception as e:
            logger.critical(f"Ошибка при отправке сообщения в чат {chat_id}: {repr(e)}", exc_info=True)
            raise
