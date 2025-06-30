from aiogram import Bot
from aiogram.types import InputFile, BufferedInputFile
from src.services.interfaces.message_sender import IMessageSender


class TelegramMessageSender(IMessageSender):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_message(self, chat_id: int, text: str, attachments: bytes | None = None) -> None:
        if attachments:
            photo = BufferedInputFile(attachments, filename="image.jpg")
            await self.bot.send_photo(chat_id, photo=photo, caption=text)
            print("Есть изображение", len(attachments))
        else:
            await self.bot.send_message(chat_id, text)