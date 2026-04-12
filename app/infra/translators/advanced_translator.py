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
                source=source_lang or "auto",
                target=target_lang
            )

            traduzido = []

            for chunk in chunks:
                print("Traduzindo chunk:", len(chunk))
                
                try:
                    traducao = translator.translate(chunk)
                    traduzido.append(traducao)
                    
                except Exception as e:
                    print("Erro ao traduzir chunk:", e)
                    traduzido.append(chunk)
                    
            return " ".join(traduzido)

        except Exception as e:
            print("Erro de Tradução:", e)
            # fail-safe
            return texto

    # ==============================
    # UTIL: divisão inteligente
    # ==============================
    def _split_text(self, texto: str):
        partes = []
        chunk_size=self.chunk_size

        for i in range(0, len(texto), chunk_size):
            partes.append(texto[i:i+chunk_size])

        return partes