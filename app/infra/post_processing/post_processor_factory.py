from app.infra.post_processing.advanced_text_post_processor import AdvancedTextPostProcessor
from app.infra.post_processing.llm_text_post_processor import LLMTextPostProcessor


def get_text_post_processor(provider: str = "advanced"):

    if provider == "advanced":
        return AdvancedTextPostProcessor()

    if provider == "llm":
        return LLMTextPostProcessor()

    raise ValueError(f"PostProcessor '{provider}' não suportado.")