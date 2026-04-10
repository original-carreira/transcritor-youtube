from abc import ABC, abstractmethod


class Translator(ABC):
    """Contrato para serviços de tradução."""

    @abstractmethod
    def traduzir(self, texto: str, source_lang: str, target_lang: str) -> str:
        """Traduz texto de um idioma para outro."""
        pass