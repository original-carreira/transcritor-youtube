from app.infra.language.simple_language_detector import SimpleLanguageDetector


def get_language_detector(provider: str = "simple"):
    """
    Factory de detectores de idioma.
    """

    if provider == "simple":
        return SimpleLanguageDetector()

    raise ValueError(f"Language detector '{provider}' não suportado.")