from deep_translator import GoogleTranslator
from app.infra.translators.translator import Translator


class SimpleTranslator(Translator):
    """Implementação básica usando Google Translate via deep-translator."""

    def traduzir(self, texto: str, source_lang: str, target_lang: str) -> str:
        if not texto:
            return ""

        try:
            translator = GoogleTranslator(
                source=source_lang or "auto",
                target=target_lang
            )

            return translator.translate(texto)

        except Exception as e:            
            # Mantém comportamento seguro (não quebra o sistema)
            return texto