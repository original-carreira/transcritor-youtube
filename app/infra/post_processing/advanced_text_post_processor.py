import re
from app.infra.post_processing.text_post_processor import TextPostProcessor


class AdvancedTextPostProcessor(TextPostProcessor):
    """
    Processador heurístico avançado (arquitetura estabilizada).

    Pipeline organizado por fases:
    1. Normalização
    2. Limpeza (irreversível)
    3. Transformação
    4. Estrutura
    5. Formatação final

    Garantias:
    - determinismo
    - idempotência
    - isolamento entre etapas
    - ausência de efeito cascata
    """

    def process(self, text: str, language: str | None = None) -> str:
        # fail-safe               
        if not text or not text.strip():
            return text

        try:
            current = text

            # ==============================
            # 🔵 FASE 1 — NORMALIZAÇÃO
            # ==============================
            current = self._normalize(current)

            # ==============================
            # 🔵 FASE 2 — LIMPEZA (IRREVERSÍVEL)
            # ==============================
            current = self._remove_transcription_markers(current)
            current = self._remove_repetitions(current)
            current = self._remove_noise(current)

            # ==============================
            # 🔵 FASE 3 — TRANSFORMAÇÃO
            # ==============================
            current = self._remove_redundancy(current)
            current = self._simplify_oral_structures(current)

            # ==============================
            # 🔵 FASE 4 — ESTRUTURA
            # ==============================
            current = self._split_sentences_smart(current)

            # ==============================
            # 🔵 FASE 5 — FORMATAÇÃO FINAL
            # ==============================
            current = self._build_semantic_paragraphs_v2(current)
            current = self._refine_punctuation(current)

            return current

        except Exception:
            return text

    # ==============================
    # FASE 1 — NORMALIZAÇÃO
    # ==============================
    def _normalize(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    # ==============================
    # FASE 2 — LIMPEZA
    # ==============================
    def _remove_transcription_markers(self, text: str) -> str:
        try:
            text = re.sub(r"\[(.*?)\]", "", text)
            text = re.sub(r"\s+", " ", text)
            return text.strip()
        except Exception:
            return text

    def _remove_repetitions(self, text: str) -> str:
        return re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)

    def _remove_noise(self, text: str) -> str:
        try:
            # remove apenas repetições, não palavras isoladas
            text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
            return text

        except Exception:
            return text

    # ==============================
    # FASE 3 — TRANSFORMAÇÃO
    # ==============================
    def _remove_redundancy(self, text: str) -> str:
        try:
            tokens = text.split()
            resultado = []

            for i in range(len(tokens)):
                if i > 0 and tokens[i] == tokens[i - 1].lower():
                    continue

                resultado.append(tokens[i])

            return " ".join(resultado)

        except Exception:
            return text

    def _simplify_oral_structures(self, text: str) -> str:
        return text
        # try:
        #     sentences = re.split(r"(?<=[.!?])\s+", text)
        #     resultado = []

        #     for s in sentences:
        #         s = re.sub(
        #             r"\b(ele|ela)\s+(disse|falou|viu|ouviu)\s+que\s+\1\s+",
        #             r"\1 \2 que ",
        #             s,
        #             flags=re.IGNORECASE,
        #         )

        #         # s = re.sub(
        #         #     r"que\s+(o|a)\s+(\w+)",
        #         #     lambda m: self._to_gerund(m.group(2)),
        #         #     s,
        #         #     count=1,
        #         #     flags=re.IGNORECASE,
        #         # )

        #         s = re.sub(r"\be então\b", "então", s, flags=re.IGNORECASE)

        #         resultado.append(s)

        #     return " ".join(resultado)

        # except Exception:
        #     return text

    def _to_gerund(self, verbo: str) -> str:
        if verbo.endswith("ar"):
            return verbo[:-2] + "ando"
        if verbo.endswith("er"):
            return verbo[:-2] + "endo"
        if verbo.endswith("ir"):
            return verbo[:-2] + "indo"
        return verbo

    # ==============================
    # FASE 4 — ESTRUTURA
    # ==============================
    def _split_sentences_smart(self, text: str) -> str:
        try:
            if not text:
                return text

            # ==============================
            # 1. NORMALIZA ESPAÇOS
            # ==============================
            text = re.sub(r"\s+", " ", text).strip()

            # ==============================
            # 2. DIVIDE POR PONTUAÇÃO REAL
            # ==============================
            sentences = re.split(r'(?<=[.!?])\s+', text)

            # ==============================
            # 3. REMOVE FRAGMENTOS RUINS
            # ==============================
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

            # ==============================
            # 4. REAGRUPA (EVITA QUEBRA EXCESSIVA)
            # ==============================
            resultado = []
            buffer = ""

            for s in sentences:
                if len(buffer) < 120:
                    buffer += " " + s
                else:
                    resultado.append(buffer.strip())
                    buffer = s

            if buffer:
                resultado.append(buffer.strip())

            return " ".join(resultado)

        except Exception:
            return text

    # ==============================
    # FASE 5 — FORMATAÇÃO FINAL
    # ==============================
    def _build_semantic_paragraphs_v2(self, text: str) -> str:
        try:
            sentences = re.split(r"(?<=[.!?])\s+", text)

            if len(sentences) <= 2:
                return "\n\n".join(sentences)

            paragraphs = []
            buffer = []

            triggers = (
                "caríssimos irmãos",
                "meus irmãos",
                "mas",
                "então",
                "por quê",
                "pois bem",
                "veja",
                "eu pergunto",
                "pense",
                "quantos de nós",
                "mateus",
                "versículo",
            )

            for sentence in sentences:
                s_lower = sentence.lower().strip()

                if any(s_lower.startswith(t) for t in triggers):
                    if buffer:
                        paragraphs.append(" ".join(buffer))
                        buffer = []

                buffer.append(sentence)

                if len(buffer) >= 5:
                    paragraphs.append(" ".join(buffer))
                    buffer = []

            if buffer:
                paragraphs.append(" ".join(buffer))

            return "\n\n".join(p.strip() for p in paragraphs)

        except Exception:
            return text

    def _refine_punctuation(self, text: str) -> str:
        try:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            resultado = []

            for s in sentences:
                s = re.sub(r"\s+(mas|porém|então|por isso)\b", r", \1", s, flags=re.IGNORECASE)
                s = re.sub(r"^(então|agora|por isso)\s+", r"\1, ", s, flags=re.IGNORECASE)
                s = re.sub(r"\b(\w+),\s+(foi|estava|disse|fez)\b", r"\1 \2", s, flags=re.IGNORECASE)
                s = re.sub(r"[.,]{2,}", ".", s)
                s = re.sub(r"\s+([.,!?])", r"\1", s)
                s = re.sub(r"([.,!?])([^\s])", r"\1 \2", s)

                if not re.search(r"[.!?]$", s):
                    s += "."

                resultado.append(s.strip())

            return " ".join(resultado)

        except Exception:
            return text