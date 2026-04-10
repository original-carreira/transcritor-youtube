from app.infra.translators.simple_translator import SimpleTranslator


def get_translator(provider: str = "simple"):
    """Factory para obtenção de tradutores."""

    if provider == "simple":
        return SimpleTranslator()

    raise ValueError(f"Translator provider '{provider}' não suportado.")