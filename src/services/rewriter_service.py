import aiohttp
from src.services.interfaces.text_rewriter import ITextRewriterService


class GeminiTextRewriterService(ITextRewriterService):
    def __init__(self, api_key: str, model: str = "google/gemini-2.5-flash-lite-preview-06-17"):
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

        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=headers, json=body) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"OpenRouter API Error: {resp.status} {text}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
