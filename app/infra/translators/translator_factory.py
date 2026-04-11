from app.infra.translators.simple_translator import SimpleTranslator
from app.infra.translators.advanced_translator import AdvancedTranslator


def get_translator(provider: str = "advanced"):
    """
    Factory de tradutores.
    """

    if provider == "simple":
        return SimpleTranslator()

    if provider == "advanced":
        return AdvancedTranslator()

    raise ValueError(f"Provider '{provider}' não suportado.")