import logging
import re
from typing import List

from app.infra.post_processing.text_post_processor import TextPostProcessor

logger = logging.getLogger(__name__)


class LLMTextPostProcessor(TextPostProcessor):
    """
    Pós-processador baseado em LLM (reescrita semântica).

    - Usa chunking para textos longos
    - Fail-safe: retorna texto original em caso de erro
    - Pronto para integração com OpenAI ou equivalente
    """

    def __init__(self, chunk_size: int = 1500):
        self.chunk_size = chunk_size

    # ==============================
    # ENTRYPOINT
    # ==============================
    def process(self, text: str, language: str | None = None) -> str:
        if not text or not text.strip():
            return text

        try:
            logger.info("LLM PostProcessor ativado")

            chunks = self._split_text(text)
            logger.debug(f"Chunks gerados: {len(chunks)}")

            processed_chunks = []

            for chunk in chunks:
                processed = self._process_chunk(chunk, language)
                processed_chunks.append(processed)

            return "\n\n".join(processed_chunks)

        except Exception as e:
            logger.warning(f"Falha no LLMTextPostProcessor: {str(e)}")
            return text

    # ==============================
    # CHUNKING (ESSENCIAL)
    # ==============================
    def _split_text(self, text: str) -> List[str]:
        """
        Divide o texto em blocos respeitando tamanho e tentando preservar estrutura.
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for p in paragraphs:
            if len(current) + len(p) < self.chunk_size:
                current += "\n\n" + p if current else p
            else:
                chunks.append(current.strip())
                current = p

        if current:
            chunks.append(current.strip())

        return chunks

    # ==============================
    # PROCESSAMENTO POR CHUNK
    # ==============================
    def _process_chunk(self, text: str, language: str | None) -> str:
        """
        Placeholder para chamada LLM.

        Aqui será integrado futuramente com OpenAI.
        """

        try:
            prompt = self._build_prompt(text, language)

            # 🔴 MOCK (SEM API REAL)
            # Substituir futuramente por chamada real
            return self._mock_llm_response(text)

        except Exception:
            return text

    # ==============================
    # PROMPT (CRÍTICO)
    # ==============================
    def _build_prompt(self, text: str, language: str | None) -> str:
        idioma = language or "português"

        return f"""
Reescreva o texto abaixo em {idioma} correto e natural.

Objetivos:
- Corrigir pontuação
- Melhorar fluidez
- Remover repetições
- Organizar frases
- Manter exatamente o mesmo significado

Regras:
- NÃO adicionar conteúdo novo
- NÃO remover informações relevantes
- NÃO resumir
- NÃO interpretar além do texto

Texto:
{text}
"""

    # ==============================
    # MOCK TEMPORÁRIO
    # ==============================
    def _mock_llm_response(self, text: str) -> str:
        """
        Simula melhoria básica (até integrar LLM real)
        """
        text = text.strip()

        # capitalização simples
        if text:
            text = text[0].upper() + text[1:]

        # pontuação básica
        if not re.search(r'[.!?]$', text):
            text += '.'

        return text