# ==============================
#           IMPORTS
# ==============================
from app.repositories.cache_repository import CacheRepository
from app.clients.youtube_client import YouTubeClient

import requests
import re
import unicodedata


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
        resultado = self.obter_transcricao(
            url,
            target_lang=target_lang if translate else None
        )

        # Caso sucesso
        if isinstance(resultado, dict):
            texto = resultado.get("transcricao")

            origem = "Cache Local" if resultado.get("from_cache") else "YouTube API"

            return {
                "text": texto,
                "segments": None,
                "source": origem,
                "success": True if texto else False,
                "error": None if texto else "Transcrição vazia",
                "titulo": resultado.get("titulo"),
                "thumbnail": resultado.get("thumbnail")
            }

        # Caso erro (string)
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
    # METADADOS
    # ==============================
    def obter_titulo_video(self, url):
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            html = response.text
            match = re.search(r'<title>(.*?)</title>', html)
            if match:
                return match.group(1).replace(" - YouTube", "").strip()
            return "titulo_indisponivel"
        except Exception:
            return "titulo_indisponivel"

    def obter_thumbnail(self, video_id):
        if not video_id:
            return None
        qualidades = ["maxresdefault", "hqdefault", "mqdefault"]
        return [f"https://img.youtube.com/vi/{video_id}/{q}.jpg" for q in qualidades]

    # ==============================
    # PIPELINE PRINCIPAL
    # ==============================
    def obter_transcricao(self, url, target_lang=None):
        video_id = self.extrair_id(url)

        if not video_id:
            return "URL inválida."

        # ==============================
        # 1. CACHE (TRANSCRIÇÃO)
        # ==============================
        cache_item = self.cache.buscar_por_video_id(video_id)

        if cache_item:
            texto = cache_item.get("transcricao")

            # ==============================
            # CACHE DE TRADUÇÃO
            # ==============================
            if target_lang and target_lang != "pt" and self.translator:
                traducao = self.cache.obter_traducao(video_id, target_lang)
                if traducao:
                    texto = traducao

            return {
                "transcricao": texto,
                "titulo": cache_item.get("titulo"),
                "thumbnail": cache_item.get("thumbnail"),
                "from_cache": True
            }

        try:
            # ==============================
            # 2. EXTRAÇÃO
            # ==============================
            transcript_list = self.youtube.fetch_transcript(video_id)

            if not transcript_list:
                return "Nenhuma transcrição encontrada."

            # ==============================
            # 3. PROCESSAMENTO
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
                return "Transcrição vazia após processamento."

            titulo = self.obter_titulo_video(url)
            thumbnail = self.obter_thumbnail(video_id)

            # ==============================
            # 4. CACHE (TRANSCRIÇÃO)
            # ==============================
            self.cache.adicionar(video_id, url, titulo, thumbnail, texto_final)

            texto_saida = texto_final

            # ==============================
            # 5. CACHE + TRADUÇÃO
            # ==============================
            if target_lang and target_lang != "pt" and self.translator:

                traducao = self.cache.obter_traducao(video_id, target_lang)

                if traducao:
                    texto_saida = traducao
                else:
                    texto_traduzido = self.translator.traduzir(
                        texto_final,
                        source_lang="pt",
                        target_lang=target_lang
                    )

                    if texto_traduzido:
                        self.cache.salvar_traducao(video_id, target_lang, texto_traduzido)
                        texto_saida = texto_traduzido

            return {
                "transcricao": texto_saida,
                "titulo": titulo,
                "thumbnail": thumbnail,
                "from_cache": False
            }

        except Exception as e:
            return f"Erro na API do YouTube: {str(e)}"