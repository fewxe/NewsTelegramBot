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
            - Сохрани смысл и ключевые факты.
            - Сделай стиль лаконичным, сжатием до главного.
            - НЕ превышай 1000 символов.
            - Если текст слишком длинный — сокращай, выкидывай повторы, переписывай кратко.
            - Итоговый текст должен помещаться в 1 Telegram сообщение.
            Вот сам исходный текст:
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
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
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
