import aiohttp
from aiohttp import ClientResponseError
from src.services.interfaces.text_rewriter import ITextRewriterService
from src.logging_config import logger


logger = logger.getChild(__name__)


class DeepSeekTextRewriterService(ITextRewriterService):
    def __init__(self, api_key: str, model: str = "deepseek/deepseek-chat-v3-0324:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def rewrite(self, text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        prompt = """
            Ты — помощник, который обрабатывает новостные тексты для публикации в Telegram.

            Твоя задача:
            - Удали любые элементы, похожие на рекламу, призывы подписаться, перейти по ссылке, упоминания спонсоров и внешних ресурсов.
            - Сохрани только суть: ключевые факты, цифры, события, имена, даты.
            - Сократи стиль до лаконичного и информационного: избегай воды и повторов.
            - Отформатируй итоговый текст для Telegram:
                • абзацы разделяй пустой строкой,
                • НЕ используй markdown или html-разметку,
                • НЕ вставляй ссылки, если они не критичны для понимания.
            - Строго не превышай 1000 символов. Если исходный текст длинный — сокращай или переписывай.
            - Итог должен быть информативным и удобочитаемым сообщением в Telegram.

            Вот исходный текст:
            """


        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt + text
                        }
                    ]
                }
            ]
        }

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(self.base_url, headers=headers, json=body) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content")
                    )
                    if not content:
                        logger.error(f"OpenRouter API returned empty content: {data}")
                        raise RuntimeError("OpenRouter API returned empty content")

                    logger.debug(f"Rewritten text length: {len(content)} chars")
                    return content

        except ClientResponseError as e:
            logger.exception(f"OpenRouter API responded with HTTP error: {e.status} {e.message}")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error during text rewriting: {repr(e)}")
            raise
