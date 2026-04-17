import re
from app.infra.post_processing.text_post_processor import TextPostProcessor

class AdvancedTextPostProcessor(TextPostProcessor):
    def process(self, text: str, language: str | None = None) -> str:
        if not text or not text.strip():
            return text

        try:
            current = text
            current = self._normalize(current)
            current = self._remove_transcription_markers(current)
            current = self._remove_repetitions(current)
            current = self._remove_noise(current)
            current = self._remove_redundancy(current)
            current = self._simplify_oral_structures(current)
            current = self._split_sentences_smart(current)
            current = self._build_semantic_paragraphs_v2(current)
            current = self._refine_punctuation(current)
            return current
        except Exception:
            return text

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip())

    def _remove_transcription_markers(self, text: str) -> str:
        return re.sub(r"\[(.*?)\]", "", text).strip()

    def _remove_repetitions(self, text: str) -> str:
        return re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)

    def _remove_noise(self, text: str) -> str:
        return self._remove_repetitions(text)

    def _remove_redundancy(self, text: str) -> str:
        tokens = text.split()
        resultado = [tokens[i] for i in range(len(tokens)) if i == 0 or tokens[i].lower() != tokens[i-1].lower()]
        return " ".join(resultado)

    def _simplify_oral_structures(self, text: str) -> str:
        # Limpa marcas de fala (né, tá, meus santos, entenderam)
        text = re.sub(r",?\s*(né|tá|sabe|entenderam|meus santos)\??(?=\s|$|[.!?,])", "", text, flags=re.IGNORECASE)
        # Transforma o ponto final antes do 'mas' em vírgula para manter o fluxo
        text = re.sub(r"\.\s+(mas|porém|contudo)\b", r", \1", text, flags=re.IGNORECASE)
        # Remove conectores de início de frase repetitivos
        text = re.sub(r"(?<=[.!?])\s*(e então|então|aí|daí|e aí)\s+", " ", text, flags=re.IGNORECASE)
        return text

    def _split_sentences_smart(self, text: str) -> str:
        # Crucial: APENAS limpa espaços. Não reagrupa para permitir que a Fase 5 quebre parágrafos.
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return " ".join([s.strip() for s in sentences if len(s.strip()) > 5])

    def _build_semantic_paragraphs_v2(self, text: str) -> str:
        try:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            if len(sentences) <= 3: return text

            paragraphs, buffer = [], []
            # Gatilhos universais de transição (incluindo 'meus irmãos' para o contexto da homilia)
            triggers = ("além disso", "por outro lado", "veja", "agora", "quando", "se", "portanto", "meus irmãos", "caríssimos")

            for sentence in sentences:
                s_lower = sentence.lower().strip()
                # QUEBRA: Se atingir 4 frases OU encontrar gatilho após 2 frases
                if len(buffer) >= 4 or (any(s_lower.startswith(t) for t in triggers) and len(buffer) >= 2):
                    paragraphs.append(" ".join(buffer))
                    buffer = []
                buffer.append(sentence)

            if buffer: paragraphs.append(" ".join(buffer))
            return "\n\n".join(p.strip() for p in paragraphs)
        except Exception:
            return text

    def _refine_punctuation(self, text: str) -> str:
        # Formatação final: espaços e maiúsculas
        text = re.sub(r"([.!?,])([^\s\d])", r"\1 \2", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
        return text
