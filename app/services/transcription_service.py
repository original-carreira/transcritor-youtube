# ==============================
# IMPORTS
# ==============================
from app.repositories.cache_repository import CacheRepository
from app.clients.youtube_client import YouTubeClient
from app.infra.post_processing.advanced_text_post_processor import AdvancedTextPostProcessor

import logging

logger = logging.getLogger("app")


class TranscriptionService:
    def __init__(self, translator=None, language_detector=None, text_post_processor=None):
        """
        Service principal de orquestração.

        Responsabilidades:
        - Coordenar transcrição
        - Orquestrar cache
        - Aplicar tradução (opcional)
        - Aplicar detecção de idioma (opcional)
        - Aplicar pós-processamento textual (opcional)
        """
        self.cache = CacheRepository()
        self.youtube = YouTubeClient()
        self.translator = translator
        self.language_detector = language_detector
        self.text_post_processor = text_post_processor or AdvancedTextPostProcessor()

    # ==============================
    # ENTRYPOINT
    # ==============================
    def process(
        self,
        url: str,
        post_process: bool = False
    ):
        logger.info(
            f"Process iniciado | url={url} | post_process={post_process}"
            )

        print("POST_PROCESS (SERVICE):", post_process)  # 👈 AQUI Retirar após teste

        # ==============================
        # EXTRAÇÃO DO VIDEO_ID
        # ==============================
        video_id = self.extrair_id(url)
        
        if not video_id:
            return self._erro("URL inválida")
        
        # ==============================
        # BUSCA NO CACHE
        # ==============================
        item_cache = self.cache.buscar_por_video_id(video_id)

        if item_cache:
            logger.info("Cache encontrado")

            texto_base = item_cache.get("text")  # 🔥 base sempre em PT
            segments = item_cache.get("segments")
            titulo = item_cache.get("titulo")
            thumbnail = item_cache.get("thumbnail")

            origem = "Cache Local"

            texto = texto_base

        else:
            # ==============================
            # BUSCA TRANSCRIÇÃO + METADATA
            # ==============================
            try:
                transcript = self.youtube.fetch_transcript(video_id)

                if not transcript:
                    return self._erro("Transcrição não encontrada")

                texto = " ".join([seg["text"] for seg in transcript])
                segments = [
                    {
                        "start": seg["start"],
                        "end": seg["start"] + seg.get("duration", 0),
                        "text": seg["text"]
                    }
                    for seg in transcript
                ]

                # 🔴 CORREÇÃO AQUI (USO CORRETO DO CLIENT)
                metadata = self.youtube.fetch_video_metadata(video_id)

                titulo = metadata.get("titulo")
                thumbnail = metadata.get("thumbnail")

                # 🔴 NORMALIZA THUMBNAIL
                if isinstance(thumbnail, list):
                    thumbnail = thumbnail[0]

                # 🔴 GARANTE TÍTULO
                titulo = titulo or url

                # ==============================
                # SALVA NO CACHE
                # ==============================
                self.cache.adicionar(video_id, url, titulo, thumbnail, texto)

                logger.info("Transcrição salva no cache")

                origem = "YouTube API"

            except Exception:
                logger.error("Erro ao obter transcrição", exc_info=True)
                return self._erro("Erro ao obter transcrição")

        # ==============================
        # DETECÇÃO DE IDIOMA (OPCIONAL)
        # ==============================
        # Detecção temporiamente desabilitada para estabilzar o sistema       
        
        # ==============================
        # TRADUÇÃO (COM CACHE)
        # ==============================
        # Tradução temporiamente desabilitada para estabilzar o sistema
                     
        # ==============================
        # PÓS-PROCESSAMENTO (OPCIONAL)
        # ==============================
        print("POST_PROCESS (SERVICE):", post_process)  # 👈 AQUI Retirar após teste
        
        if post_process and self.text_post_processor and texto:
            
            print("ENTROU NO POST_PROCESS") # 👈 Retirar após teste
            
            print("ANTES:", texto[:100])  # 👈 ANTES
            
            try:
                logger.info("Aplicando pós-processamento")
                
                print("DEPOIS:", texto[:100])  # 👈 DEPOIS Retirar após teste

                texto= self.text_post_processor.process(texto)

            except Exception:
                logger.warning("Falha no pós-processamento")

        # ==============================
        # RETORNO PADRONIZADO
        # ==============================
        return {
            "text": texto,
            "segments": segments,
            "source": origem,
            "success": True,
            "error": None,
            "titulo": titulo,
            "thumbnail": thumbnail
        }    
    
    # ==============================
    # EXTRAIR ID
    # ==============================
    def extrair_id(self, url: str):
        try:
            import re

            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
            return match.group(1) if match else None

        except Exception:
            return None

    # ==============================
    # ERRO PADRONIZADO
    # ==============================
    def _erro(self, mensagem: str):
        return {
            "text": None,
            "segments": None,
            "source": "Sistema",
            "success": False,
            "error": mensagem,
            "titulo": None,
            "thumbnail": None
        }