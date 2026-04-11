# ==============================
# IMPORTS
# ==============================
from app.repositories.cache_repository import CacheRepository
from app.clients.youtube_client import YouTubeClient

import logging

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, translator=None, language_detector=None, text_post_processor=None):
        """
        Service principal de orquestração.

        Responsabilidades:
        - Coordenar transcrição (API ou cache via YouTubeClient)
        - Aplicar detecção de idioma (opcional)
        - Aplicar tradução (texto + segments)
        - Aplicar pós-processamento textual
        - Garantir persistência no cache
        - Padronizar resposta para UI
        """

        self.cache = CacheRepository()
        self.youtube = YouTubeClient()
        self.translator = translator
        self.language_detector = language_detector
        self.text_post_processor = text_post_processor

    # ==============================
    # ENTRYPOINT PRINCIPAL
    # ==============================
    def process(
        self,
        url: str,
        translate: bool = False,
        target_lang: str | None = None,
        source_lang: str | None = None,
        post_process: bool = False
    ):
        """
        Executa pipeline completo:

        fluxo:
        YouTubeClient → (cache/API)
        → detecção idioma (opcional)
        → tradução (opcional)
        → pós-processamento (opcional)
        → retorno padronizado
        """

        logger.info(
            f"Process iniciado | url={url} | translate={translate} | target_lang={target_lang} | post_process={post_process}"
        )

        # ==============================
        # OBTÉM DADOS (CACHE OU API)
        # ==============================
        resultado = self.youtube.get_transcription(url)

        if not isinstance(resultado, dict):
            logger.error(f"Erro no processamento: {resultado}")

            return {
                "text": None,
                "segments": None,
                "source": "api",
                "success": False,
                "error": resultado,
                "titulo": None,
                "thumbnail": None
            }

        texto = resultado.get("transcricao")
        segments = resultado.get("segments")

        if not texto:
            logger.warning("Transcrição vazia")

        # ==============================
        # DETECÇÃO DE IDIOMA (OPCIONAL)
        # ==============================
        detected_lang = None

        if translate and not source_lang and self.language_detector and texto:
            try:
                detected_lang = self.language_detector.detect(texto)
                logger.info(f"Idioma detectado: {detected_lang}")
            except Exception:
                logger.warning("Falha na detecção de idioma")

        # fallback seguro
        source_lang_final = source_lang or detected_lang or "pt"

        # ==============================
        # TRADUÇÃO (TEXTO + SEGMENTS)
        # ==============================
        if translate and self.translator and texto:
            logger.info(f"Tradução ativada | target_lang={target_lang}")

            try:
                texto_traduzido = self.translator.traduzir(
                    texto,
                    source_lang=source_lang_final,
                    target_lang=target_lang
                )

                if texto_traduzido:
                    texto = texto_traduzido

                # 🔥 TRADUZ SEGMENTS (CRÍTICO)
                if segments:
                    segments = self._translate_segments(
                        segments,
                        target_lang,
                        source_lang_final
                    )

            except Exception:
                logger.warning("Falha na tradução, mantendo original")

        # ==============================
        # PÓS-PROCESSAMENTO
        # ==============================
        if post_process and self.text_post_processor and texto:
            try:
                logger.info(
                    f"Pós-processamento aplicado | provider={type(self.text_post_processor).__name__}"
                )

                language = target_lang if translate else source_lang_final

                texto_processado = self.text_post_processor.process(
                    texto,
                    language=language
                )

                if texto_processado:
                    texto = texto_processado

            except Exception:
                logger.warning("Falha no pós-processamento")

        # ==============================
        # SALVAR NO CACHE (GARANTIA)
        # ==============================
        try:
            if texto:
                self.cache.salvar({
                    "video_id": resultado.get("video_id"),
                    "url": url,
                    "titulo": resultado.get("titulo"),
                    "thumbnail": resultado.get("thumbnail"),
                    "transcricao": texto
                })
                logger.info("Transcrição salva no cache")

        except Exception:
            logger.warning("Falha ao salvar no cache")

        # ==============================
        # ORIGEM
        # ==============================
        origem = "cache" if resultado.get("from_cache") else "api"

        # ==============================
        # RESPOSTA PADRÃO (CONTRATO)
        # ==============================
        return {
            "text": texto,
            "segments": segments,
            "source": origem,
            "success": True if texto else False,
            "error": None if texto else "Transcrição vazia",
            "titulo": resultado.get("titulo"),
            "thumbnail": resultado.get("thumbnail")
        }

    # ==============================
    # TRADUÇÃO DE SEGMENTS
    # ==============================
    def _translate_segments(self, segments, target_lang, source_lang=None):
        """
        Traduz segments preservando sincronização temporal.
        """

        if not segments:
            return segments

        try:
            logger.info(f"Traduzindo segments | qtd={len(segments)}")

            textos = [seg["text"] for seg in segments]
            separador = "\n|||SEG|||\n"

            texto_unico = separador.join(textos)

            texto_traduzido = self.translator.traduzir(
                texto_unico,
                source_lang=source_lang,
                target_lang=target_lang
            )

            if not texto_traduzido:
                return segments

            textos_traduzidos = texto_traduzido.split(separador)

            if len(textos_traduzidos) != len(segments):
                logger.warning("Mismatch na tradução de segments")
                return segments

            novos = []

            for seg, txt in zip(segments, textos_traduzidos):
                novos.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": txt.strip()
                })

            return novos

        except Exception:
            logger.warning("Erro traduzindo segments")
            return segments