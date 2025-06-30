from src.domain.entities import News
from src.dto.channel_dto import ChannelDTO
from src.services.interfaces.message_sender import IMessageSender
from src.services.channel_service import ChannelService
from src.services.interfaces.text_rewriter import ITextRewriterService
from src.services.news_source.news_source import NewsSource


class MessageService:
    def __init__(self, message_sender: IMessageSender, channel_service: ChannelService, rewrite_service: ITextRewriterService):
        self.message_sender = message_sender
        self.channel_service = channel_service
        self.rewrite_service = rewrite_service

    async def send_one_news_to_channel(self, channel: ChannelDTO, feed_service: NewsSource):
        print(f"[MessageService] Начинаем обработку канала ID={channel.id}")

        all_news = []
        for rss_url in channel.rss_links:
            print(f"[MessageService] Загружаем новости из RSS: {rss_url}")
            news = await feed_service.fetch_latest_news(rss_url)
            print(f"[MessageService] Найдено {len(news)} новостей")
            all_news.extend(news)

        all_news.sort(key=lambda n: getattr(n, "published_at", "") or "", reverse=False)
        print(f"[MessageService] Всего собрано новостей: {len(all_news)}")

        sent_links = await self.channel_service.get_last_sent_links(channel.id)
        print(f"[MessageService] Уже отправленные ссылки: {sent_links}")

        next_news = None
        for item in all_news:
            if item.link not in sent_links:
                next_news = item
                print(f"[MessageService] Нашли новую новость: {item.link}")
                break

        if not next_news:
            print(f"[MessageService] Нет новых новостей для канала ID={channel.id}")
            return

        title = getattr(next_news, "title", "") or ""
        description = getattr(next_news, "description", "") or ""
        print(f"[MessageService] Заголовок: {repr(title)}")
        print(f"[MessageService] Описание: {repr(description)}")

        message = f"{title}\n{description}"
        print(f"[MessageService] Исходный текст:\n{message}")

        try:
            rewritten_message = await self.rewrite_service.rewrite(message)
            print(f"[MessageService] Переписанный текст:\n{repr(rewritten_message)}")
        except Exception as e:
            print(f"[MessageService] Ошибка в rewrite_service: {repr(e)}")
            return

        try:
            print(f"[MessageService] Отправка сообщения в канал {channel.id}...")
            await self.message_sender.send_message(
                channel.id,
                rewritten_message,
                getattr(next_news, "image_link", None)
            )
            print(f"[MessageService] Сообщение успешно отправлено в канал ID={channel.id}")
        except Exception as e:
            print(f"[MessageService] Ошибка при отправке: {repr(e)}")
            return

        try:
            await self.channel_service.add_last_sent_links(channel.id, next_news.link)
            print(f"[MessageService] Ссылка новости добавлена в отправленные.")
        except Exception as e:
            print(f"[MessageService] Ошибка при сохранении ссылки: {repr(e)}")
