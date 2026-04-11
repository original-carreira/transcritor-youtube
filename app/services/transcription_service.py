# ==============================
#           IMPORTS
# ==============================
from app.repositories.cache_repository import CacheRepository
from app.clients.youtube_client import YouTubeClient

import requests
import re
import logging
import unicodedata

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, translator=None):
        """
        Service principal de orquestração.

        Responsabilidades:
        - Coordenar transcrição
        - Aplicar limpeza
        - Orquestrar cache
        - Aplicar tradução (opcional)
        """
        self.cache = CacheRepository()
        self.youtube = YouTubeClient()
        self.translator = translator

    # ==============================
    # ENTRYPOINT
    # ==============================
    def process(self, url: str, translate: bool = False, target_lang: str | None = None):
        """
        Orquestra todo o fluxo e padroniza a resposta.
        """
        logger.info(f"Process iniciado | url={url} | translate={translate} | target_lang={target_lang}")

        resultado = self.obter_transcricao(
            url,
            target_lang=target_lang if translate else None
        )

        if isinstance(resultado, dict):
            texto = resultado.get("transcricao")
            segments = resultado.get("segments")

            origem = "Cache Local" if resultado.get("from_cache") else "YouTube API"

            # ==============================
            # TRADUÇÃO (TEXT + SEGMENTS)
            # ==============================
            if translate and self.translator and texto:
                logger.info(f"Tradução ativada | target_lang={target_lang}")

                try:
                    texto_traduzido = self.translator.traduzir(
                        texto,
                        source_lang="pt",
                        target_lang=target_lang
                    )

                    if texto_traduzido:
                        texto = texto_traduzido

                    if segments:
                        segments = self._translate_segments(segments, target_lang)

                except Exception:
                    logger.warning("Falha na tradução no process(), mantendo texto original")

            return {
                "text": texto,
                "segments": segments,
                "source": origem,
                "success": True if texto else False,
                "error": None if texto else "Transcrição vazia",
                "titulo": resultado.get("titulo"),
                "thumbnail": resultado.get("thumbnail")
            }

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

    # ==============================
    # TRADUÇÃO DE SEGMENTS (BATCH)
    # ==============================
    def _translate_segments(self, segments, target_lang):
        if not segments:
            return segments

        try:
            logger.info(f"Traduzindo segments | quantidade={len(segments)}")

            textos = [seg["text"] for seg in segments]

            separador = "\n|||SEG|||\n"
            texto_unico = separador.join(textos)

            texto_traduzido = self.translator.traduzir(
                texto_unico,
                source_lang="pt",
                target_lang=target_lang
            )

            if not texto_traduzido:
                logger.warning("Falha ao traduzir segments (texto vazio)")
                return segments

            textos_traduzidos = texto_traduzido.split(separador)

            if len(textos_traduzidos) != len(segments):
                logger.warning("Mismatch na tradução de segments")
                return segments

            novos_segments = []
            for seg, texto in zip(segments, textos_traduzidos):
                novos_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": texto.strip()
                })

            return novos_segments

        except Exception:
            logger.warning("Erro na tradução de segments")
            return segments

    # ==============================
    # UTILITÁRIOS
    # ==============================
    def extrair_id(self, url):
        match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
        return match.group(1) if match else None

    def limpar_texto(self, texto):
        texto = re.sub(r'\[[^\]]*\]', '', texto)
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    def normalizar_sentencas(self, texto):
        if not texto:
            return ""
        texto = texto[0].upper() + texto[1:]
        if not re.search(r'[.!?]["\']?$', texto):
            texto += '.'
        texto = re.sub(
            r'([.!?]\s+)([a-záéíóúâêôãõç])',
            lambda m: m.group(1) + m.group(2).upper(),
            texto
        )
        return texto.strip()

    def remover_repeticoes(self, texto):
        return re.sub(r'\b(\w{2,})\s+\1\b', r'\1', texto, flags=re.IGNORECASE)

    def quebra_por_gatilhos(self, texto):
        gatilhos = [
            "E agora", "E aqui", "Por isso", "Mas", "Então", "Porque",
            "Por que", "Além disso", "No entanto", "Entretanto",
            "Contudo", "Ou seja", "Hoje", "E nós vemos", "Enfim",
            "Concluindo"
        ]

        for g in gatilhos:
            padrao = r'([.!?]\s+)(' + re.escape(g) + r')'
            texto = re.sub(padrao, r'\1\n\n\2', texto, flags=re.IGNORECASE)

        texto = re.sub(r'\n{3,}', '\n\n', texto)
        return texto.strip()

    def agrupar_por_tempo(self, transcript, pausa=2.0, max_palavras=80):
        paragrafos = []
        bloco = []
        ultimo_tempo_fim = None
        contador_palavras = 0

        for item in transcript:
            try:
                texto = item['text'].strip()
                tempo_inicio = item['start']
                duracao = item.get('duration', 0) or 0
            except (TypeError, KeyError, AttributeError):
                texto = item.text.strip()
                tempo_inicio = item.start
                duracao = getattr(item, 'duration', 0) or 0

            if not texto:
                continue

            tempo_fim = tempo_inicio + duracao
            qtd_palavras = len(texto.split())

            quebra_tempo = (
                ultimo_tempo_fim is not None and
                (tempo_inicio - ultimo_tempo_fim > pausa)
            )
            quebra_tamanho = (contador_palavras + qtd_palavras) > max_palavras

            if (quebra_tempo or quebra_tamanho) and bloco:
                paragrafos.append(" ".join(bloco))
                bloco = []
                contador_palavras = 0

            bloco.append(texto)
            contador_palavras += qtd_palavras
            ultimo_tempo_fim = tempo_fim

        if bloco:
            paragrafos.append(" ".join(bloco))

        return paragrafos

    # ==============================
    # PIPELINE PRINCIPAL
    # ==============================
    def obter_transcricao(self, url, target_lang=None):
        video_id = self.extrair_id(url)

        logger.info(f"Iniciando processamento | video_id={video_id}")

        if not video_id:
            logger.warning("URL inválida fornecida")
            return "URL inválida."

        # ==============================
        # CACHE
        # ==============================
        cache_item = self.cache.buscar_por_video_id(video_id)

        if cache_item:
            logger.info(f"Cache HIT | video_id={video_id}")

            return {
                "transcricao": cache_item.get("transcricao"),
                "titulo": cache_item.get("titulo"),
                "thumbnail": cache_item.get("thumbnail"),
                "segments": None,
                "from_cache": True
            }

        logger.info(f"Cache MISS | video_id={video_id}")

        try:
            # ==============================
            # EXTRAÇÃO
            # ==============================
            logger.info("Buscando transcrição via YouTubeClient")

            transcript_list = self.youtube.fetch_transcript(video_id)

            if not transcript_list:
                logger.warning("Nenhuma transcrição encontrada")
                return "Nenhuma transcrição encontrada."

            # ==============================
            # PROCESSAMENTO
            # ==============================
            paragrafos = self.agrupar_por_tempo(transcript_list)
            processados = []

            for p in paragrafos:
                p = self.limpar_texto(p)
                p = self.remover_repeticoes(p)
                p = self.normalizar_sentencas(p)
                p = self.quebra_por_gatilhos(p)

                if p:
                    processados.append(p)

            texto_final = "\n\n".join(processados)

            if not texto_final:
                logger.warning("Texto vazio após processamento")
                return "Transcrição vazia após processamento."

            metadata = self.youtube.fetch_video_metadata(video_id)

            titulo = metadata.get("titulo")
            thumbnail = metadata.get("thumbnail")
            
            

            # ==============================
            # CACHE SAVE
            # ==============================
            logger.info(f"Salvando no cache | video_id={video_id}")

            self.cache.adicionar(video_id, url, titulo, thumbnail, texto_final)

            return {
                "transcricao": texto_final,
                "titulo": titulo,
                "thumbnail": thumbnail,
                "segments": None,
                "from_cache": False
            }

        except Exception as e:
            logger.error(f"Erro na API do YouTube: {str(e)}")
            return f"Erro na API do YouTube: {str(e)}"