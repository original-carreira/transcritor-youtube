from langdetect import detect, DetectorFactory
from app.infra.language.language_detector import LanguageDetector

# Garante consistência (langdetect é não determinístico por padrão)
DetectorFactory.seed = 0


class SimpleLanguageDetector(LanguageDetector):
    """
    Implementação básica de detecção de idioma.
    """

    def detect(self, text: str) -> str | None:
        if not text or not text.strip():
            return None

        try:
            lang = detect(text)
            return lang

        except Exception:
            # fail-safe obrigatório
            return None