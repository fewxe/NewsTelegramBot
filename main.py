import asyncio
from aiogram import Bot, Dispatcher
from src.application.channel_manager import ChannelManager
from src.bot.admin_handlers import admin_router
from src.bot.handlers import channel_events_router
from src.bot.middlewares.check_admin_middleware import AdminCheckMiddleware
from src.infrastructure.models import Base
from src.infrastructure.db import engine
from src.services.news_source.feed_service import FeedService
from src.services.channel_service import ChannelService
from src.services.message_service import MessageService
from src.services.telegram_message_sender import TelegramMessageSender
from src.infrastructure.repositories import ChannelRepository
from src.services.rewriter_service import GeminiTextRewriterService
from src.infrastructure.db import SessionLocal
from src.services.news_scheduler import NewsScheduler
from dotenv import load_dotenv
import os


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    if BOT_TOKEN is None or API_KEY is None:
        raise ValueError("Environment variables are not set!")
    
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    feed_service = FeedService()
    async with SessionLocal() as session:
        repo = ChannelRepository(session)
        channel_service = ChannelService(repo)
        message_sender = TelegramMessageSender(bot)
        rewrite_service = GeminiTextRewriterService(API_KEY)
        message_service = MessageService(message_sender, channel_service, rewrite_service)
        news_scheduler = NewsScheduler(channel_service, feed_service, message_service)
        channel_manager = ChannelManager(channel_service, news_scheduler)
        
        dp.include_router(admin_router(channel_manager))
        dp.include_router(channel_events_router(bot, channel_service))
        
        await news_scheduler.schedule_all()
        news_scheduler.start()
        
        middleware = AdminCheckMiddleware(bot, channel_service)
        dp.message.middleware(middleware)

        await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
