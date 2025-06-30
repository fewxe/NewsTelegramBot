from abc import ABC, abstractmethod


class ITextRewriterService(ABC):
    @abstractmethod
    async def rewrite(self, text: str) -> str:
        ...