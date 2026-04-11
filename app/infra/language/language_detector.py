from abc import ABC, abstractmethod


class LanguageDetector(ABC):
    """
    Contrato para detecção de idioma.
    """

    @abstractmethod
    def detect(self, text: str) -> str | None:
        """
        Detecta o idioma do texto.

        Retorna:
            Código do idioma (ex: 'en', 'pt') ou None em caso de falha.
        """
        pass