from app.infra.translators.translator import Translator
from deep_translator import GoogleTranslator


class AdvancedTranslator(Translator):
    """
    Tradutor com melhor qualidade:
    - processamento em blocos
    - preservação de contexto
    """

    def __init__(self, chunk_size=3000):
        self.chunk_size = chunk_size

    def traduzir(self, texto: str, source_lang: str, target_lang: str) -> str:
        if not texto:
            return ""

        try:
            chunks = self._split_text(texto)

            translator = GoogleTranslator(
                source=source_lang,
                target=target_lang
            )

            traduzido = []

            for chunk in chunks:
                traduzido.append(translator.translate(chunk))

            return " ".join(traduzido)

        except Exception:
            # fail-safe
            return texto

    # ==============================
    # UTIL: divisão inteligente
    # ==============================
    def _split_text(self, texto: str):
        """
        Divide o texto em blocos grandes, preservando contexto.
        """
        partes = []
        atual = ""

        for linha in texto.split("\n\n"):
            if len(atual) + len(linha) < self.chunk_size:
                atual += " " + linha
            else:
                partes.append(atual.strip())
                atual = linha

        if atual:
            partes.append(atual.strip())

        return partes