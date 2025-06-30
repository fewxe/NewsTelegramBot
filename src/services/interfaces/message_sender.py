from abc import ABC, abstractmethod

class IMessageSender(ABC):
    @abstractmethod
    async def send_message(self, chat_id: int, text: str, attachments: bytes | None) -> None:
        ...