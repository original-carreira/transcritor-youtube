import re
from app.infra.post_processing.text_post_processor import TextPostProcessor


class AdvancedTextPostProcessor(TextPostProcessor):
    """
    Processador avançado de texto (LLM-ready).

    Atualmente:
    - heurístico (regex + regras simples)
    Futuro:
    - integração com LLM
    """

    def process(self, text: str, language: str | None = None) -> str:
        if not text or not text.strip():
            return text

        try:
            texto = text.strip()

            # ==============================
            # NORMALIZAÇÃO BÁSICA
            # ==============================
            texto = self._normalize_spacing(texto)

            # ==============================
            # CAPITALIZAÇÃO
            # ==============================
            texto = self._capitalize_sentences(texto)

            # ==============================
            # PONTUAÇÃO
            # ==============================
            texto = self._fix_punctuation(texto)

            # ==============================
            # QUEBRAS ARTIFICIAIS
            # ==============================
            texto = self._fix_line_breaks(texto)

            return texto

        except Exception:
            # fail-safe
            return text

    # ==============================
    # HELPERS
    # ==============================

    def _normalize_spacing(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _capitalize_sentences(self, text: str) -> str:
        if not text:
            return text

        text = text[0].upper() + text[1:]

        text = re.sub(
            r'([.!?]\s+)([a-z])',
            lambda m: m.group(1) + m.group(2).upper(),
            text
        )

        return text

    def _fix_punctuation(self, text: str) -> str:
        # adiciona ponto final se necessário
        if not re.search(r'[.!?]$', text):
            text += '.'

        # corrige múltiplos pontos
        text = re.sub(r'\.{2,}', '.', text)

        return text

    def _fix_line_breaks(self, text: str) -> str:
        # remove quebras artificiais excessivas
        text = re.sub(r'\n{2,}', '\n\n', text)

        # opcional: juntar linhas muito fragmentadas
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

        return text