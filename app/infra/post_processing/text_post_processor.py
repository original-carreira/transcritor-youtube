from abc import ABC, abstractmethod


class TextPostProcessor(ABC):
    """
    Contrato para pós-processamento textual.
    """

    @abstractmethod
    def process(self, text: str, language: str | None = None) -> str:
        """
        Refina linguisticamente o texto.

        Regras:
        - preservar significado original
        - melhorar fluidez
        - corrigir pontuação e capitalização

        Retorno:
            Texto refinado ou original em caso de falha
        """
        pass