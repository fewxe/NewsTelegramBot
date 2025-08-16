from src.domain.entities import News
from src.dto.channel_dto import ChannelDTO
from src.services.interfaces.message_sender import IMessageSender
from src.services.channel_service import ChannelService
from src.services.interfaces.text_rewriter import ITextRewriterService
from src.services.news_source.news_source import NewsSource
from src.logging_config import logger

logger = logger.getChild(__name__)

class MessageService:
    def __init__(self, message_sender: IMessageSender, channel_service: ChannelService, rewrite_service: ITextRewriterService):
        self.message_sender = message_sender
        self.channel_service = channel_service
        self.rewrite_service = rewrite_service

    async def send_one_news_to_channel(self, channel: ChannelDTO, feed_service: NewsSource):
        logger.info(f"Start processing channel ID={channel.id}")

        all_news = []
        for rss_url in channel.rss_links:
            try:
                logger.info(f"Fetching news from RSS feed: {rss_url}")
                news = await feed_service.fetch_latest_news(rss_url)
                logger.info(f"Fetched {len(news)} news items from {rss_url}")
                all_news.extend(news)
            except Exception as e:
                logger.error(f"Failed to fetch news from {rss_url}: {repr(e)}", exc_info=True)

        if not all_news:
            logger.info(f"No news fetched for channel ID={channel.id}")
            return

        all_news.sort(key=lambda n: getattr(n, "published_at", "") or "", reverse=False)
        logger.info(f"Total collected news items: {len(all_news)}")

        sent_links = await self.channel_service.get_last_sent_links(channel.id)
        logger.info(f"Already sent links for channel ID={channel.id}: {sent_links}")

        next_news = None
        for item in all_news:
            if item.link not in sent_links:
                next_news = item
                logger.info(f"Found new news item to send: {item.link}")
                break

        if not next_news:
            logger.info(f"No new news to send for channel ID={channel.id}")
            return

        title = getattr(next_news, "title", "") or ""
        description = getattr(next_news, "description", "") or ""
        logger.debug(f"News title: {repr(title)}")
        logger.debug(f"News description: {repr(description)}")

        message = f"{title}\n{description}"
        logger.debug(f"Original message text:\n{message}")

        try:
            rewritten_message = await self.rewrite_service.rewrite(message)
            logger.info(f"Rewritten message text:\n{repr(rewritten_message)}")
        except Exception as e:
            logger.critical(f"Rewrite service failed: {repr(e)}", exc_info=True)
            return

        try:
            logger.info(f"Sending message to channel ID={channel.id}...")
            await self.message_sender.send_message(
                channel.id,
                rewritten_message,
                getattr(next_news, "image_link", None)
            )
            logger.info(f"Message successfully sent to channel ID={channel.id}")
        except Exception as e:
            logger.critical(f"Failed to send message: {repr(e)}", exc_info=True)
            return

        try:
            await self.channel_service.add_last_sent_links(channel.id, next_news.link)
            logger.info(f"Added news link to sent history for channel ID={channel.id}")
        except Exception as e:
            logger.critical(f"Failed to save sent news link: {repr(e)}", exc_info=True)
