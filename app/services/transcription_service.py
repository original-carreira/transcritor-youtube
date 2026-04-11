# ==============================
#           IMPORTS
# =============================
from app.repositories.cache_repository import CacheRepository
from app.clients.youtube_client import YouTubeClient

import youtube_transcript_api
import requests
import re
import unicodedata
import json
import os

class TranscriptionService:
    def __init__(self, translator=None):
        self.cache = CacheRepository()
        self.youtube = YouTubeClient()
        self.translator = translator
    
    def process(self, url: str, translate: bool = False, target_lang: str | None = None):
        """Orquestra todo o fluxo de transcrição."""
        resultado = self.obter_transcricao(url)
        
        # Se for um dicionário vindo do cache ou do fluxo de extração
        if isinstance(resultado, dict):
            texto = resultado.get("transcricao") or resultado.get("text")
            
            # ==============================
            # TRADUÇÃO (OPCIONAL)
            # ==============================
            if translate and self.translator and texto:
                try:
                    texto_traduzido = self.translator.translate(texto, target_lang)
                    if texto_traduzido:
                        texto = texto_traduzido
                except Exception:
                    # fail-safe: mantém texto original
                    pass
            
                                
            # LÓGICA DE ORIGEM: 
            # Se o dicionário tiver 'video_id', sabemos que veio do nosso CacheRepository
            origem = "Cache Local" if "video_id" in resultado else "YouTube API"
            
            return {
                "text": texto,
                "segments": None,
                "source": origem,
                "success": True if texto else False,
                "error": None if texto else "Transcrição vazia",
                "titulo": resultado.get("titulo"),
                "thumbnail": resultado.get("thumbnail")
                }
            
        # Caso seja string (erro ou fallback antigo)
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
    # UTILITÁRIOS BÁSICOS
    # ==============================
    def extrair_id(self, url):
        """Extrai o ID do vídeo a partir da URL do YouTube.
        Ex: https://youtube.com → ABC123"""
        match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
        return match.group(1) if match else None

    # ==============================
    # LIMPEZA INICIAL DO TEXTO
    # ==============================
    def limpar_texto(self, texto):
        """Remove:
        - textos entre colchetes [música], [aplausos]
        - espaços duplicados"""
        texto = re.sub(r'\[[^\]]*\]', '', texto)
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    # ==============================
    # NORMALIZAÇÃO DE SENTENÇAS
    # ==============================
    def normalizar_sentencas(self, texto):
        """Ajusta:
        - primeira letra maiúscula
        - garante ponto final
        - capitalização após pontuação"""
        if not texto:
            return ""
        texto = texto[0].upper() + texto[1:]
        # Garante pontuação final
        if not re.search(r'[.!?]["\']?$', texto):
            texto += '.'
        # Capitaliza após pontuação
        texto = re.sub(r'([.!?]\s+)([a-záéíóúâêôãõç])',
                       lambda m: m.group(1) + m.group(2).upper(),
                       texto)
        return texto.strip()

    # ==============================
    # REMOÇÃO DE REPETIÇÕES
    # ==============================
    def remover_repeticoes(self, texto):
        """Remove palavras repetidas consecutivas."""
        return re.sub(r'\b(\w{2,})\s+\1\b', r'\1', texto, flags=re.IGNORECASE)

    # ==============================
    # QUEBRA POR GATILHOS SEMÂNTICOS
    # ==============================
    def quebra_por_gatilhos(self, texto):
        """Insere quebras de parágrafo com base em palavras-chave
        que indicam mudança de ideia."""
        gatilhos = ["E agora", "E aqui", "Por isso", "Mas", "Então", "Porque",
                    "Por que", "Além disso", "No entanto", "Entretanto",
                    "Contudo", "Ou seja", "Hoje", "E nós vemos", "Enfim",
                    "Concluindo"]
        for g in gatilhos:
            padrao = r'([.!?]\s+)(' + re.escape(g) + r')'
            texto = re.sub(padrao, r'\1\n\n\2', texto, flags=re.IGNORECASE)
        # Remove quebras excessivas
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        return texto.strip()

    # ==============================
    # AGRUPAMENTO POR TEMPO
    # ==============================
    def agrupar_por_tempo(self, transcript, pausa=2.0, max_palavras=80):
        """Agrupa falas em parágrafos com base em:
        - pausas entre falas
        - limite de palavras"""
        paragrafos = []
        bloco = []
        ultimo_tempo_fim = None
        contador_palavras = 0
        
        for item in transcript:
             # ✅ O PULO DO GATO: Se não for um dicionário, acessamos como objeto
            # Isso evita o erro "'FetchedTranscriptSnippet' object has no attribute 'get'"
            try:
                texto = item['text'].strip()
                tempo_inicio = item['start']
                duracao = item.get('duration', 0) or 0
            except (TypeError, KeyError, AttributeError):
                # Fallback para acesso como atributo de objeto
                texto = item.text.strip()
                tempo_inicio = item.start
                duracao = getattr(item, 'duration', 0) or 0

            if not texto:
                continue

            tempo_fim = tempo_inicio + duracao
            qtd_palavras = len(texto.split())
            
            
            if not texto:
                continue
            
            tempo_fim = tempo_inicio + duracao
            qtd_palavras = len(texto.split())

            quebra_tempo = (ultimo_tempo_fim is not None and 
                           (tempo_inicio - ultimo_tempo_fim > pausa))
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
    # CORREÇÕES ESTRUTURAIS
    # ==============================
    def corrigir_pontos_quebrados(self, texto):
        """ Corrige:
        - palavras curtas quebradas com ponto
        Ex: "no. Caminho" → "no Caminho" """
        excecoes = r'(?![Ss]r|[Dd]r|[Aa]v|[Aa]rt|[Cc]ap|[Ii]d)'
        padrao = r'\b(' + excecoes + r'\w{1,3})\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ])'
        texto = re.sub(padrao, r'\1 \2', texto)
        texto = re.sub(r'\s+\.\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])', '. ', texto)
        return texto.strip()

    def corrigir_quebra_apos_dois_pontos(self, texto):
        """ Corrige quebra após ":" """
        return re.sub(r':\s*[\r\n]+', ': ', texto)

    def limpar_quebras_indevidas(self, texto):
        """ Junta frases quebradas incorretamente após conectivos """
        conectivos = r'\b(a|de|do|da|e|o|que|com|em|um|uma|para|por|como)\b'
        texto = re.sub(f'{conectivos}\.\s*\n+\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ])',
                       lambda m: f"{m.group(1)} {m.group(2)}",
                       texto,
                       flags=re.IGNORECASE)
        texto = re.sub(r'\b(?!(?:Sr|Dr|Av)\.)(\w{1,3})\.\s*\n+\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ])',
                       r'\1 \2',
                       texto)
        return texto

    def corrigir_quebras_artificiais(self, texto):
        """ Junta quebras de linha indevidas sem pontuação. """
        return re.sub(r'([^.!?])\s*\n\s*\n\s*', r'\1 ', texto)

    # ==============================
    # METADADOS DO VÍDEO
    # ==============================
    def obter_titulo_video(self, url):
        """ Obtém o título do vídeo via HTML."""
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            html = response.text
            match = re.search(r'<title>(.*?)</title>', html)
            if match:
                return match.group(1).replace(" - YouTube", "").strip()
            return "titulo_indisponivel"
        except Exception:
            return "titulo_indisponivel"

    def limpar_nome_arquivo(self, nome):
        """Normaliza o nome para uso em arquivos:
        - remove acentos
        - remove caracteres inválidos
        - limita tamanho sem cortar palavras"""
        nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
        nome = re.sub(r'[\\/*?:"<>|,]', '', nome)
        nome = re.sub(r'\s+', '_', nome)
        nome = re.sub(r'_+', '_', nome)
        nome = nome.strip('_')
        palavras = nome.split('_')
        resultado = []
        for palavra in palavras:
            if len("_".join(resultado + [palavra])) <= 60:
                resultado.append(palavra)
            else:
                break
        return "_".join(resultado).lower()

    def obter_thumbnail(self, video_id):
        """Retorna lista de thumbnails em diferentes qualidades
        (fallback automático no frontend)."""
        if not video_id:
            return None
        qualidades = ["maxresdefault", "hqdefault", "mqdefault"]
        return [f"https://img.youtube.com/vi/{video_id}/{q}.jpg" for q in qualidades]

    # ==============================
    # FUNÇÃO PRINCIPAL
    # ==============================
    def obter_transcricao(self, url):
        """Pipeline completo com extração robusta usando o método estático de lista."""
        video_id = self.extrair_id(url)
        
        # 1. Verifica Cache
        cache_item = self.cache.buscar_por_video_id(video_id)
        if cache_item:
            cache_item["video_id"] = video_id 
            return cache_item
            
        if not video_id:
            return "URL inválida."
            
        try:
            # 2. CHAMADA ESTÁTICA (Funciona em 99% das versões)
            # Nota: O método é get_transcript (no singular) e pertence à classe
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Dentro do obter_transcricao no TranscriptionService
            transcript_list = self.youtube.fetch_transcript(video_id)
            
            if not transcript_list:
                return "Nenhuma transcrição encontrada."
                
            # 3. Agrupamento (Passamos a lista de dicionários retornada)
            paragrafos_brutos = self.agrupar_por_tempo(transcript_list)
            paragrafos_processados = []
            
            # 4. Pipeline de Limpeza (Mantendo sua lógica original)
            for p in paragrafos_brutos:
                p_limpo = self.limpar_texto(p)
                p_limpo = self.limpar_quebras_indevidas(p_limpo)
                p_limpo = self.corrigir_pontos_quebrados(p_limpo)
                p_limpo = self.remover_repeticoes(p_limpo)
                p_limpo = self.normalizar_sentencas(p_limpo)
                p_limpo = self.quebra_por_gatilhos(p_limpo)
                p_limpo = self.corrigir_quebra_apos_dois_pontos(p_limpo)
                p_limpo = self.corrigir_quebras_artificiais(p_limpo)
                
                if p_limpo:
                    paragrafos_processados.append(p_limpo)
            
            texto_final = "\n\n".join(paragrafos_processados)
            
            if not texto_final:
                return "Transcrição obtida, mas vazia após limpeza."

            titulo = self.obter_titulo_video(url)
            thumbnail = self.obter_thumbnail(video_id)
            
            # 5. Salva no Cache
            self.cache.adicionar(video_id, url, titulo, thumbnail, texto_final)
            
            return {
                "transcricao": texto_final,
                "titulo": titulo,
                "thumbnail": thumbnail
            }
            
        except Exception as e:
            return f"Erro na API do YouTube: {str(e)}"

   
